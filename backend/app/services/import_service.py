"""
Import Service - データインポートサービス

Handles importing factories and employees from JSON and Excel files.
Provides preview/validation before actual import.
"""
import json
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from openpyxl import load_workbook
from sqlalchemy.orm import Session

from app.models.factory import Factory, FactoryLine
from app.models.employee import Employee


class ImportValidationError:
    """Represents a validation error during import."""

    def __init__(self, row: int, field: str, message: str, value: Any = None):
        self.row = row
        self.field = field
        self.message = message
        self.value = value

    def to_dict(self) -> dict:
        return {
            "row": self.row,
            "field": self.field,
            "message": self.message,
            "value": str(self.value) if self.value is not None else None
        }


class ImportResult:
    """Result of an import operation."""

    def __init__(self):
        self.success = False
        self.total_rows = 0
        self.imported_count = 0
        self.updated_count = 0
        self.skipped_count = 0
        self.factories_created = 0
        self.lines_created = 0
        self.errors: List[ImportValidationError] = []
        self.preview_data: List[dict] = []
        self.message = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "total_rows": self.total_rows,
            "imported_count": self.imported_count,
            "updated_count": self.updated_count,
            "skipped_count": self.skipped_count,
            "factories_created": self.factories_created,
            "lines_created": self.lines_created,
            "errors": [e.to_dict() for e in self.errors],
            "preview_data": self.preview_data[:100],  # Limit preview
            "message": self.message
        }


class ImportService:
    """Service for importing data from files."""

    def __init__(self, db: Session):
        self.db = db

    # ========================================
    # FACTORY IMPORT - JSON
    # ========================================

    def import_factories_from_json(self, json_data: Union[str, bytes, dict, List[dict]]) -> ImportResult:
        """
        Import factories from JSON data.

        Supports both single factory object or array of factories.
        Creates Factory and associated FactoryLine records.

        Args:
            json_data: JSON string, bytes, dict, or list of dicts

        Returns:
            ImportResult with summary of import operation
        """
        result = ImportResult()

        try:
            # Parse JSON if needed
            if isinstance(json_data, (str, bytes)):
                if isinstance(json_data, bytes):
                    json_data = json_data.decode('utf-8')
                data = json.loads(json_data)
            else:
                data = json_data

            # Handle both single object and array
            if isinstance(data, dict):
                factories_data = [data]
            else:
                factories_data = data

            result.total_rows = len(factories_data)

            for idx, factory_data in enumerate(factories_data, 1):
                try:
                    # Validate factory data
                    validated, errors = self._validate_factory(idx, factory_data)
                    if errors:
                        result.errors.extend(errors)
                        result.skipped_count += 1
                        continue

                    # Extract factory info
                    company_name = factory_data.get("company_name") or factory_data.get("派遣先名")
                    plant_name = factory_data.get("plant_name") or factory_data.get("工場名")

                    if not company_name or not plant_name:
                        result.skipped_count += 1
                        continue

                    # Generate factory_id
                    factory_id = f"{company_name}_{plant_name}".replace(" ", "_")

                    # Check if factory exists
                    existing_factory = self.db.query(Factory).filter(
                        Factory.factory_id == factory_id
                    ).first()

                    if existing_factory:
                        # Update existing factory
                        self._update_factory_from_json(existing_factory, factory_data)
                        factory = existing_factory
                        result.updated_count += 1
                    else:
                        # Create new factory
                        factory = self._create_factory_from_json(factory_id, factory_data)
                        self.db.add(factory)
                        self.db.flush()  # Get factory.id
                        result.factories_created += 1
                        result.imported_count += 1

                    # Handle FactoryLines
                    lines_data = factory_data.get("lines", factory_data.get("ライン", []))
                    if lines_data:
                        lines_created = self._create_factory_lines(factory, lines_data)
                        result.lines_created += lines_created

                except Exception as e:
                    result.errors.append(
                        ImportValidationError(idx, "factory", f"工場インポートエラー: {str(e)}")
                    )
                    result.skipped_count += 1

            # Commit all changes
            self.db.commit()
            result.success = True
            result.message = (
                f"インポート完了: 工場{result.factories_created}件作成, "
                f"{result.updated_count}件更新, ライン{result.lines_created}件作成, "
                f"スキップ{result.skipped_count}件"
            )

        except json.JSONDecodeError as e:
            self.db.rollback()
            result.errors.append(
                ImportValidationError(0, "file", f"JSON解析エラー: {str(e)}")
            )
            result.message = "JSONファイルの形式が正しくありません"
        except Exception as e:
            self.db.rollback()
            result.errors.append(
                ImportValidationError(0, "import", f"インポートエラー: {str(e)}")
            )
            result.message = f"インポート失敗: {str(e)}"

        return result

    def _create_factory_from_json(self, factory_id: str, data: dict) -> Factory:
        """Create a new Factory from JSON data."""

        def parse_date_field(val):
            if val is None:
                return None
            if isinstance(val, date):
                return val
            if isinstance(val, datetime):
                return val.date()
            if isinstance(val, str):
                try:
                    return datetime.strptime(val, "%Y-%m-%d").date()
                except ValueError:
                    return None
            return None

        def parse_time_field(val):
            if val is None:
                return None
            if isinstance(val, str):
                try:
                    return datetime.strptime(val, "%H:%M").time()
                except ValueError:
                    return None
            return None

        conflict_date = parse_date_field(
            data.get("conflict_date") or data.get("抵触日")
        )

        return Factory(
            factory_id=factory_id,
            # 派遣先情報
            company_name=data.get("company_name") or data.get("派遣先名", ""),
            company_address=data.get("company_address") or data.get("派遣先住所"),
            company_phone=data.get("company_phone") or data.get("派遣先電話"),
            company_fax=data.get("company_fax") or data.get("派遣先FAX"),
            # 工場情報
            plant_name=data.get("plant_name") or data.get("工場名", ""),
            plant_address=data.get("plant_address") or data.get("工場住所"),
            plant_phone=data.get("plant_phone") or data.get("工場電話"),
            # 派遣先責任者
            client_responsible_name=data.get("client_responsible_name") or data.get("派遣先責任者"),
            client_responsible_department=data.get("client_responsible_department") or data.get("派遣先責任者部署"),
            client_responsible_phone=data.get("client_responsible_phone") or data.get("派遣先責任者電話"),
            # 派遣先苦情担当者
            client_complaint_name=data.get("client_complaint_name") or data.get("派遣先苦情担当者"),
            client_complaint_department=data.get("client_complaint_department") or data.get("派遣先苦情担当部署"),
            client_complaint_phone=data.get("client_complaint_phone") or data.get("派遣先苦情担当電話"),
            # 派遣元情報
            dispatch_responsible_name=data.get("dispatch_responsible_name") or data.get("派遣元責任者"),
            dispatch_responsible_department=data.get("dispatch_responsible_department") or data.get("派遣元責任者部署"),
            dispatch_responsible_phone=data.get("dispatch_responsible_phone") or data.get("派遣元責任者電話"),
            dispatch_complaint_name=data.get("dispatch_complaint_name") or data.get("派遣元苦情担当者"),
            dispatch_complaint_department=data.get("dispatch_complaint_department") or data.get("派遣元苦情担当部署"),
            dispatch_complaint_phone=data.get("dispatch_complaint_phone") or data.get("派遣元苦情担当電話"),
            # スケジュール
            work_hours_description=data.get("work_hours_description") or data.get("就業時間"),
            break_time_description=data.get("break_time_description") or data.get("休憩時間"),
            calendar_description=data.get("calendar_description") or data.get("カレンダー"),
            day_shift_start=parse_time_field(data.get("day_shift_start") or data.get("日勤開始")),
            day_shift_end=parse_time_field(data.get("day_shift_end") or data.get("日勤終了")),
            night_shift_start=parse_time_field(data.get("night_shift_start") or data.get("夜勤開始")),
            night_shift_end=parse_time_field(data.get("night_shift_end") or data.get("夜勤終了")),
            break_minutes=int(data.get("break_minutes", data.get("休憩時間分", 60))),
            # 時間外労働
            overtime_description=data.get("overtime_description") or data.get("時間外労働"),
            overtime_max_hours_day=self._parse_decimal(data.get("overtime_max_hours_day") or data.get("時間外上限日")),
            overtime_max_hours_month=self._parse_decimal(data.get("overtime_max_hours_month") or data.get("時間外上限月")),
            overtime_max_hours_year=self._parse_int(data.get("overtime_max_hours_year") or data.get("時間外上限年")),
            overtime_special_max_month=self._parse_decimal(data.get("overtime_special_max_month") or data.get("特別条項月")),
            overtime_special_count_year=self._parse_int(data.get("overtime_special_count_year") or data.get("特別条項回数")),
            # 休日労働
            holiday_work_description=data.get("holiday_work_description") or data.get("休日労働"),
            holiday_work_max_days_month=self._parse_int(data.get("holiday_work_max_days_month") or data.get("休日労働上限")),
            # 抵触日
            conflict_date=conflict_date,
            # 支払条件
            closing_date=data.get("closing_date") or data.get("締め日"),
            payment_date=data.get("payment_date") or data.get("支払日"),
            bank_account=data.get("bank_account") or data.get("振込先"),
            worker_closing_date=data.get("worker_closing_date") or data.get("労働者締め日"),
            worker_payment_date=data.get("worker_payment_date") or data.get("労働者支払日"),
            worker_calendar=data.get("worker_calendar") or data.get("労働者カレンダー"),
            # 協定
            agreement_period=parse_date_field(data.get("agreement_period") or data.get("協定期間")),
            agreement_explainer=data.get("agreement_explainer") or data.get("説明者"),
            # その他
            time_unit_minutes=self._parse_decimal(data.get("time_unit_minutes", data.get("時間単位", 15))),
            notes=data.get("notes") or data.get("備考"),
            is_active=data.get("is_active", True)
        )

    def _update_factory_from_json(self, factory: Factory, data: dict):
        """Update existing factory with JSON data."""

        def parse_date_field(val):
            if val is None:
                return None
            if isinstance(val, date):
                return val
            if isinstance(val, datetime):
                return val.date()
            if isinstance(val, str):
                try:
                    return datetime.strptime(val, "%Y-%m-%d").date()
                except ValueError:
                    return None
            return None

        # Update fields if provided
        if data.get("company_address") or data.get("派遣先住所"):
            factory.company_address = data.get("company_address") or data.get("派遣先住所")
        if data.get("company_phone") or data.get("派遣先電話"):
            factory.company_phone = data.get("company_phone") or data.get("派遣先電話")
        if data.get("plant_address") or data.get("工場住所"):
            factory.plant_address = data.get("plant_address") or data.get("工場住所")
        if data.get("plant_phone") or data.get("工場電話"):
            factory.plant_phone = data.get("plant_phone") or data.get("工場電話")
        if data.get("conflict_date") or data.get("抵触日"):
            factory.conflict_date = parse_date_field(
                data.get("conflict_date") or data.get("抵触日")
            )
        if data.get("client_responsible_name") or data.get("派遣先責任者"):
            factory.client_responsible_name = (
                data.get("client_responsible_name") or data.get("派遣先責任者")
            )
        if data.get("client_complaint_name") or data.get("派遣先苦情担当者"):
            factory.client_complaint_name = (
                data.get("client_complaint_name") or data.get("派遣先苦情担当者")
            )
        if data.get("closing_date") or data.get("締め日"):
            factory.closing_date = data.get("closing_date") or data.get("締め日")
        if data.get("payment_date") or data.get("支払日"):
            factory.payment_date = data.get("payment_date") or data.get("支払日")

    def _create_factory_lines(self, factory: Factory, lines_data: List[dict]) -> int:
        """
        Create FactoryLine records for a factory.

        Args:
            factory: Factory instance
            lines_data: List of line dictionaries

        Returns:
            Number of lines created
        """
        lines_created = 0

        for idx, line_data in enumerate(lines_data):
            try:
                # Generate line_id if not provided
                line_id = line_data.get("line_id") or line_data.get("ラインID") or f"Line-{idx+1}"

                # Check if line already exists
                existing_line = self.db.query(FactoryLine).filter(
                    FactoryLine.factory_id == factory.id,
                    FactoryLine.line_id == line_id
                ).first()

                if existing_line:
                    # Update existing line
                    self._update_factory_line(existing_line, line_data)
                else:
                    # Create new line
                    line = FactoryLine(
                        factory_id=factory.id,
                        line_id=line_id,
                        department=line_data.get("department") or line_data.get("配属先"),
                        line_name=line_data.get("line_name") or line_data.get("ライン名"),
                        # 指揮命令者
                        supervisor_department=line_data.get("supervisor_department") or line_data.get("指揮命令者部署"),
                        supervisor_name=line_data.get("supervisor_name") or line_data.get("指揮命令者"),
                        supervisor_phone=line_data.get("supervisor_phone") or line_data.get("指揮命令者電話"),
                        # 業務内容
                        job_description=line_data.get("job_description") or line_data.get("仕事内容"),
                        job_description_detail=line_data.get("job_description_detail") or line_data.get("仕事内容詳細"),
                        responsibility_level=line_data.get("responsibility_level") or line_data.get("責任程度", "通常業務"),
                        # 料金
                        hourly_rate=self._parse_decimal(line_data.get("hourly_rate") or line_data.get("時給")),
                        billing_rate=self._parse_decimal(line_data.get("billing_rate") or line_data.get("請求単価")),
                        overtime_rate=self._parse_decimal(line_data.get("overtime_rate") or line_data.get("時間外単価")),
                        night_rate=self._parse_decimal(line_data.get("night_rate") or line_data.get("深夜単価")),
                        holiday_rate=self._parse_decimal(line_data.get("holiday_rate") or line_data.get("休日単価")),
                        # その他
                        display_order=self._parse_int(line_data.get("display_order", idx)),
                        is_active=line_data.get("is_active", True)
                    )
                    self.db.add(line)
                    lines_created += 1

            except Exception as e:
                # Skip this line but continue with others
                continue

        return lines_created

    def _update_factory_line(self, line: FactoryLine, data: dict):
        """Update existing FactoryLine with new data."""
        if data.get("department") or data.get("配属先"):
            line.department = data.get("department") or data.get("配属先")
        if data.get("line_name") or data.get("ライン名"):
            line.line_name = data.get("line_name") or data.get("ライン名")
        if data.get("supervisor_name") or data.get("指揮命令者"):
            line.supervisor_name = data.get("supervisor_name") or data.get("指揮命令者")
        if data.get("job_description") or data.get("仕事内容"):
            line.job_description = data.get("job_description") or data.get("仕事内容")
        if data.get("hourly_rate") or data.get("時給"):
            line.hourly_rate = self._parse_decimal(data.get("hourly_rate") or data.get("時給"))
        if data.get("billing_rate") or data.get("請求単価"):
            line.billing_rate = self._parse_decimal(data.get("billing_rate") or data.get("請求単価"))

    # ========================================
    # EMPLOYEE IMPORT - JSON
    # ========================================

    def import_employees_from_json(self, json_data: Union[str, bytes, dict, List[dict]]) -> ImportResult:
        """
        Import employees/candidates from JSON data.

        Important field mappings:
        - "単価" (tanka) → billing_rate (what factory pays us)
        - "時給" (jikyuu) → hourly_rate (what we pay employee)
        - Margin = billing_rate - hourly_rate

        Args:
            json_data: JSON string, bytes, dict, or list of dicts

        Returns:
            ImportResult with summary of import operation
        """
        result = ImportResult()

        try:
            # Parse JSON if needed
            if isinstance(json_data, (str, bytes)):
                if isinstance(json_data, bytes):
                    json_data = json_data.decode('utf-8')
                data = json.loads(json_data)
            else:
                data = json_data

            # Handle both single object and array
            if isinstance(data, dict):
                employees_data = [data]
            else:
                employees_data = data

            result.total_rows = len(employees_data)

            for idx, emp_data in enumerate(employees_data, 1):
                try:
                    # Validate employee data
                    validated, errors = self._validate_employee_json(idx, emp_data)
                    if errors:
                        result.errors.extend(errors)
                        result.skipped_count += 1
                        continue

                    # Get employee number
                    employee_number = str(emp_data.get("employee_number") or emp_data.get("社員番号", "")).strip()

                    if not employee_number:
                        result.errors.append(
                            ImportValidationError(idx, "employee_number", "社員番号は必須です")
                        )
                        result.skipped_count += 1
                        continue

                    # Check if employee exists
                    existing_employee = self.db.query(Employee).filter(
                        Employee.employee_number == employee_number
                    ).first()

                    if existing_employee:
                        # Update existing employee
                        self._update_employee_from_json(existing_employee, emp_data)
                        result.updated_count += 1
                    else:
                        # Create new employee
                        employee = self._create_employee_from_json(emp_data)
                        self.db.add(employee)
                        result.imported_count += 1

                except Exception as e:
                    result.errors.append(
                        ImportValidationError(idx, "employee", f"従業員インポートエラー: {str(e)}")
                    )
                    result.skipped_count += 1

            # Commit all changes
            self.db.commit()
            result.success = True
            result.message = (
                f"インポート完了: 新規{result.imported_count}件, "
                f"更新{result.updated_count}件, スキップ{result.skipped_count}件"
            )

        except json.JSONDecodeError as e:
            self.db.rollback()
            result.errors.append(
                ImportValidationError(0, "file", f"JSON解析エラー: {str(e)}")
            )
            result.message = "JSONファイルの形式が正しくありません"
        except Exception as e:
            self.db.rollback()
            result.errors.append(
                ImportValidationError(0, "import", f"インポートエラー: {str(e)}")
            )
            result.message = f"インポート失敗: {str(e)}"

        return result

    def _validate_employee_json(self, row: int, data: dict) -> Tuple[dict, List[ImportValidationError]]:
        """Validate a single employee record from JSON."""
        errors = []

        employee_number = data.get("employee_number") or data.get("社員番号")
        if not employee_number:
            errors.append(ImportValidationError(row, "employee_number", "社員番号は必須です"))

        full_name_kanji = data.get("full_name_kanji") or data.get("氏名")
        if not full_name_kanji:
            errors.append(ImportValidationError(row, "full_name_kanji", "氏名は必須です"))

        full_name_kana = data.get("full_name_kana") or data.get("カナ")
        if not full_name_kana:
            errors.append(ImportValidationError(row, "full_name_kana", "カナは必須です"))

        hire_date = data.get("hire_date") or data.get("入社日")
        if not hire_date:
            errors.append(ImportValidationError(row, "hire_date", "入社日は必須です"))

        # Validate dates
        date_fields = {
            "hire_date": "入社日",
            "termination_date": "退社日",
            "date_of_birth": "生年月日",
            "visa_expiry_date": "ビザ期限"
        }

        for field_en, field_jp in date_fields.items():
            val = data.get(field_en) or data.get(field_jp)
            if val and isinstance(val, str):
                try:
                    datetime.strptime(val, "%Y-%m-%d")
                except ValueError:
                    errors.append(
                        ImportValidationError(row, field_en, f"{field_jp}の日付形式が正しくありません", val)
                    )

        return data, errors

    def _create_employee_from_json(self, data: dict) -> Employee:
        """
        Create new Employee from JSON data.

        Important field mappings:
        - "単価" (tanka) → billing_rate (what factory pays us)
        - "時給" (jikyuu) → hourly_rate (what we pay employee)
        """

        def parse_date_field(val):
            if val is None:
                return None
            if isinstance(val, date):
                return val
            if isinstance(val, datetime):
                return val.date()
            if isinstance(val, str):
                try:
                    return datetime.strptime(val, "%Y-%m-%d").date()
                except ValueError:
                    return None
            return None

        def parse_bool_field(val):
            if val is None:
                return True  # Default to True for insurance
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.lower() in ['true', '1', 'yes', 'はい', '○', '◯', 'あり']
            return bool(val)

        # Important: Map 単価 and 時給 correctly
        # 単価 (tanka) = billing_rate (what factory pays us)
        # 時給 (jikyuu) = hourly_rate (what we pay employee)
        billing_rate = self._parse_decimal(
            data.get("billing_rate") or data.get("単価") or data.get("請求単価")
        )
        hourly_rate = self._parse_decimal(
            data.get("hourly_rate") or data.get("時給")
        )

        # Determine nationality (Japanese vs foreigner)
        nationality = data.get("nationality") or data.get("国籍")
        if not nationality:
            # Default to Vietnamese if not specified
            nationality = "ベトナム"

        # Status
        termination_date = parse_date_field(data.get("termination_date") or data.get("退社日"))
        status = "resigned" if termination_date else data.get("status", "active")

        return Employee(
            # 識別情報
            employee_number=str(data.get("employee_number") or data.get("社員番号", "")).strip(),
            hakenmoto_id=data.get("hakenmoto_id") or data.get("派遣元管理番号"),
            rirekisho_id=data.get("rirekisho_id") or data.get("履歴書ID"),
            # 基本情報
            full_name_kanji=data.get("full_name_kanji") or data.get("氏名", ""),
            full_name_kana=data.get("full_name_kana") or data.get("カナ", ""),
            full_name_romaji=data.get("full_name_romaji") or data.get("ローマ字"),
            gender=data.get("gender") or data.get("性別"),
            date_of_birth=parse_date_field(data.get("date_of_birth") or data.get("生年月日")),
            age=self._parse_int(data.get("age") or data.get("年齢")),
            nationality=nationality,
            # 連絡先
            postal_code=data.get("postal_code") or data.get("郵便番号"),
            address=data.get("address") or data.get("住所"),
            phone=data.get("phone") or data.get("電話番号"),
            mobile=data.get("mobile") or data.get("携帯電話"),
            email=data.get("email") or data.get("メール"),
            emergency_contact_name=data.get("emergency_contact_name") or data.get("緊急連絡先氏名"),
            emergency_contact_phone=data.get("emergency_contact_phone") or data.get("緊急連絡先電話"),
            emergency_contact_relationship=data.get("emergency_contact_relationship") or data.get("続柄"),
            # 雇用情報
            hire_date=parse_date_field(data.get("hire_date") or data.get("入社日")) or date.today(),
            termination_date=termination_date,
            termination_reason=data.get("termination_reason") or data.get("退社理由"),
            status=status,
            contract_type=data.get("contract_type") or data.get("契約種類"),
            employment_type=data.get("employment_type") or data.get("雇用形態"),
            # 派遣先情報
            company_name=data.get("company_name") or data.get("派遣先"),
            plant_name=data.get("plant_name") or data.get("工場"),
            department=data.get("department") or data.get("配属先"),
            line_name=data.get("line_name") or data.get("ライン"),
            position=data.get("position") or data.get("職種"),
            # 給与情報 (IMPORTANT!)
            hourly_rate=hourly_rate,  # 時給 - what we pay employee
            billing_rate=billing_rate,  # 単価 - what factory pays us
            transportation_allowance=self._parse_decimal(data.get("transportation_allowance") or data.get("交通費", 0)),
            # 在留資格
            visa_type=data.get("visa_type") or data.get("在留資格"),
            visa_status=data.get("visa_status") or data.get("在留資格状態"),
            visa_expiry_date=parse_date_field(data.get("visa_expiry_date") or data.get("ビザ期限")),
            zairyu_card_number=data.get("zairyu_card_number") or data.get("在留カード番号"),
            zairyu_card_expiry=parse_date_field(data.get("zairyu_card_expiry") or data.get("在留カード有効期限")),
            passport_number=data.get("passport_number") or data.get("パスポート番号"),
            passport_expiry=parse_date_field(data.get("passport_expiry") or data.get("パスポート有効期限")),
            # 保険情報
            has_employment_insurance=parse_bool_field(data.get("has_employment_insurance") or data.get("雇用保険")),
            employment_insurance_number=data.get("employment_insurance_number") or data.get("雇用保険番号"),
            has_health_insurance=parse_bool_field(data.get("has_health_insurance") or data.get("健康保険")),
            health_insurance_number=data.get("health_insurance_number") or data.get("健康保険番号"),
            has_pension_insurance=parse_bool_field(data.get("has_pension_insurance") or data.get("厚生年金")),
            pension_insurance_number=data.get("pension_insurance_number") or data.get("厚生年金番号"),
            has_workers_comp=parse_bool_field(data.get("has_workers_comp") or data.get("労災保険")),
            # 有給休暇
            yukyu_total=self._parse_int(data.get("yukyu_total") or data.get("有給合計", 0)),
            yukyu_used=self._parse_int(data.get("yukyu_used") or data.get("有給使用", 0)),
            yukyu_remaining=self._parse_int(data.get("yukyu_remaining") or data.get("有給残", 0)),
            yukyu_grant_date=parse_date_field(data.get("yukyu_grant_date") or data.get("有給付与日")),
            # 住居情報
            apartment_name=data.get("apartment_name") or data.get("アパート名"),
            apartment_room=data.get("apartment_room") or data.get("部屋番号"),
            apartment_rent=self._parse_decimal(data.get("apartment_rent") or data.get("家賃")),
            is_corporate_housing=parse_bool_field(data.get("is_corporate_housing") or data.get("社宅")),
            housing_subsidy=self._parse_decimal(data.get("housing_subsidy") or data.get("住宅手当", 0)),
            # 銀行口座
            bank_name=data.get("bank_name") or data.get("銀行名"),
            bank_branch=data.get("bank_branch") or data.get("支店名"),
            bank_account_type=data.get("bank_account_type") or data.get("口座種別"),
            bank_account_number=data.get("bank_account_number") or data.get("口座番号"),
            bank_account_holder=data.get("bank_account_holder") or data.get("口座名義"),
            # 資格・免許
            qualifications=data.get("qualifications") or data.get("資格"),
            drivers_license=data.get("drivers_license") or data.get("運転免許"),
            drivers_license_expiry=parse_date_field(data.get("drivers_license_expiry") or data.get("運転免許有効期限")),
            forklift_license=parse_bool_field(data.get("forklift_license") or data.get("フォークリフト")),
            # その他
            notes=data.get("notes") or data.get("備考"),
            photo_url=data.get("photo_url") or data.get("写真URL")
        )

    def _update_employee_from_json(self, employee: Employee, data: dict):
        """Update existing employee with JSON data."""

        def parse_date_field(val):
            if val is None:
                return None
            if isinstance(val, date):
                return val
            if isinstance(val, datetime):
                return val.date()
            if isinstance(val, str):
                try:
                    return datetime.strptime(val, "%Y-%m-%d").date()
                except ValueError:
                    return None
            return None

        # Update basic info
        if data.get("full_name_kanji") or data.get("氏名"):
            employee.full_name_kanji = data.get("full_name_kanji") or data.get("氏名")
        if data.get("full_name_kana") or data.get("カナ"):
            employee.full_name_kana = data.get("full_name_kana") or data.get("カナ")
        if data.get("full_name_romaji") or data.get("ローマ字"):
            employee.full_name_romaji = data.get("full_name_romaji") or data.get("ローマ字")

        # Update assignment
        if data.get("company_name") or data.get("派遣先"):
            employee.company_name = data.get("company_name") or data.get("派遣先")
        if data.get("plant_name") or data.get("工場"):
            employee.plant_name = data.get("plant_name") or data.get("工場")
        if data.get("department") or data.get("配属先"):
            employee.department = data.get("department") or data.get("配属先")
        if data.get("line_name") or data.get("ライン"):
            employee.line_name = data.get("line_name") or data.get("ライン")

        # Update rates (IMPORTANT!)
        hourly_rate_val = data.get("hourly_rate") or data.get("時給")
        if hourly_rate_val:
            employee.hourly_rate = self._parse_decimal(hourly_rate_val)

        billing_rate_val = data.get("billing_rate") or data.get("単価") or data.get("請求単価")
        if billing_rate_val:
            employee.billing_rate = self._parse_decimal(billing_rate_val)

        # Update visa info
        if data.get("visa_type") or data.get("在留資格"):
            employee.visa_type = data.get("visa_type") or data.get("在留資格")
        visa_expiry = data.get("visa_expiry_date") or data.get("ビザ期限")
        if visa_expiry:
            employee.visa_expiry_date = parse_date_field(visa_expiry)

        # Update termination
        termination = data.get("termination_date") or data.get("退社日")
        if termination:
            employee.termination_date = parse_date_field(termination)
            if employee.termination_date:
                employee.status = "resigned"

        # Update contact info
        if data.get("address") or data.get("住所"):
            employee.address = data.get("address") or data.get("住所")
        if data.get("phone") or data.get("電話番号"):
            employee.phone = data.get("phone") or data.get("電話番号")
        if data.get("mobile") or data.get("携帯電話"):
            employee.mobile = data.get("mobile") or data.get("携帯電話")

    # ========================================
    # FACTORY IMPORT - EXCEL (Existing)
    # ========================================

    def preview_factories_json(self, content: bytes) -> ImportResult:
        """Preview factory data from JSON file."""
        result = ImportResult()

        try:
            data = json.loads(content.decode('utf-8'))

            # Handle both single object and array
            if isinstance(data, dict):
                factories = [data]
            else:
                factories = data

            result.total_rows = len(factories)

            for idx, factory_data in enumerate(factories, 1):
                validated, errors = self._validate_factory(idx, factory_data)
                result.errors.extend(errors)

                # Add to preview with validation status
                preview_item = {
                    "row": idx,
                    "company_name": factory_data.get("company_name", factory_data.get("派遣先名", "")),
                    "plant_name": factory_data.get("plant_name", factory_data.get("工場名", "")),
                    "conflict_date": factory_data.get("conflict_date", factory_data.get("抵触日", "")),
                    "is_valid": len(errors) == 0,
                    "errors": [e.message for e in errors],
                    "_raw": factory_data
                }
                result.preview_data.append(preview_item)

            result.success = len(result.errors) == 0
            result.message = f"{result.total_rows}件の工場データを読み込みました" if result.success else f"{len(result.errors)}件のエラーがあります"

        except json.JSONDecodeError as e:
            result.errors.append(ImportValidationError(0, "file", f"JSON解析エラー: {str(e)}"))
            result.message = "JSONファイルの形式が正しくありません"
        except Exception as e:
            result.errors.append(ImportValidationError(0, "file", f"エラー: {str(e)}"))
            result.message = f"ファイル読み込みエラー: {str(e)}"

        return result

    def preview_factories_excel(self, content: bytes) -> ImportResult:
        """Preview factory data from Excel file."""
        result = ImportResult()

        try:
            df = pd.read_excel(BytesIO(content), engine='openpyxl')
            result.total_rows = len(df)

            # Map Japanese column names to English
            column_mapping = {
                '派遣先名': 'company_name',
                '会社名': 'company_name',
                '工場名': 'plant_name',
                '工場住所': 'plant_address',
                '抵触日': 'conflict_date',
                '派遣先責任者': 'client_responsible_name',
                '派遣先苦情担当者': 'client_complaint_name',
                '締め日': 'closing_date',
                '支払日': 'payment_date',
            }

            df = df.rename(columns=column_mapping)

            for idx, row in df.iterrows():
                row_num = idx + 2  # Excel row (1-indexed + header)
                factory_data = row.to_dict()

                # Clean NaN values
                factory_data = {k: (None if pd.isna(v) else v) for k, v in factory_data.items()}

                validated, errors = self._validate_factory(row_num, factory_data)
                result.errors.extend(errors)

                preview_item = {
                    "row": row_num,
                    "company_name": factory_data.get("company_name", ""),
                    "plant_name": factory_data.get("plant_name", ""),
                    "conflict_date": str(factory_data.get("conflict_date", "")) if factory_data.get("conflict_date") else "",
                    "is_valid": len([e for e in errors if e.row == row_num]) == 0,
                    "errors": [e.message for e in errors if e.row == row_num],
                    "_raw": factory_data
                }
                result.preview_data.append(preview_item)

            result.success = len(result.errors) == 0
            result.message = f"{result.total_rows}件の工場データを読み込みました" if result.success else f"{len(result.errors)}件のエラーがあります"

        except Exception as e:
            result.errors.append(ImportValidationError(0, "file", f"Excelエラー: {str(e)}"))
            result.message = f"Excelファイル読み込みエラー: {str(e)}"

        return result

    def import_factories(self, preview_data: List[dict], mode: str = "create") -> ImportResult:
        """
        Actually import factories after preview confirmation.

        Args:
            preview_data: Validated data from preview
            mode: "create" (skip existing), "update" (update existing), "sync" (delete missing)
        """
        result = ImportResult()
        result.total_rows = len(preview_data)

        try:
            for item in preview_data:
                if not item.get("is_valid", False):
                    result.skipped_count += 1
                    continue

                raw_data = item.get("_raw", {})
                factory_id = f"{raw_data.get('company_name', '')}_{raw_data.get('plant_name', '')}".replace(" ", "_")

                # Check if exists
                existing = self.db.query(Factory).filter(Factory.factory_id == factory_id).first()

                if existing:
                    if mode in ["update", "sync"]:
                        # Update existing
                        self._update_factory(existing, raw_data)
                        result.updated_count += 1
                    else:
                        result.skipped_count += 1
                else:
                    # Create new
                    factory = self._create_factory(factory_id, raw_data)
                    self.db.add(factory)
                    result.imported_count += 1

            self.db.commit()
            result.success = True
            result.message = f"インポート完了: 新規{result.imported_count}件, 更新{result.updated_count}件, スキップ{result.skipped_count}件"

        except Exception as e:
            self.db.rollback()
            result.errors.append(ImportValidationError(0, "import", f"インポートエラー: {str(e)}"))
            result.message = f"インポート失敗: {str(e)}"

        return result

    def _validate_factory(self, row: int, data: dict) -> Tuple[dict, List[ImportValidationError]]:
        """Validate a single factory record."""
        errors = []

        company_name = data.get("company_name") or data.get("派遣先名")
        plant_name = data.get("plant_name") or data.get("工場名")

        if not company_name:
            errors.append(ImportValidationError(row, "company_name", "派遣先名は必須です"))

        if not plant_name:
            errors.append(ImportValidationError(row, "plant_name", "工場名は必須です"))

        # Validate conflict_date if present
        conflict_date = data.get("conflict_date") or data.get("抵触日")
        if conflict_date:
            try:
                if isinstance(conflict_date, str):
                    datetime.strptime(conflict_date, "%Y-%m-%d")
            except ValueError:
                errors.append(ImportValidationError(row, "conflict_date", "抵触日の形式が正しくありません (YYYY-MM-DD)", conflict_date))

        return data, errors

    def _create_factory(self, factory_id: str, data: dict) -> Factory:
        """Create a new Factory from import data."""
        conflict_date = data.get("conflict_date") or data.get("抵触日")
        if isinstance(conflict_date, str):
            conflict_date = datetime.strptime(conflict_date, "%Y-%m-%d").date()
        elif isinstance(conflict_date, datetime):
            conflict_date = conflict_date.date()

        return Factory(
            factory_id=factory_id,
            company_name=data.get("company_name") or data.get("派遣先名", ""),
            company_address=data.get("company_address") or data.get("派遣先住所"),
            company_phone=data.get("company_phone") or data.get("派遣先電話"),
            plant_name=data.get("plant_name") or data.get("工場名", ""),
            plant_address=data.get("plant_address") or data.get("工場住所"),
            plant_phone=data.get("plant_phone") or data.get("工場電話"),
            client_responsible_name=data.get("client_responsible_name") or data.get("派遣先責任者"),
            client_responsible_department=data.get("client_responsible_department") or data.get("派遣先責任者部署"),
            client_complaint_name=data.get("client_complaint_name") or data.get("派遣先苦情担当者"),
            client_complaint_department=data.get("client_complaint_department") or data.get("派遣先苦情担当部署"),
            dispatch_responsible_name=data.get("dispatch_responsible_name") or data.get("派遣元責任者"),
            dispatch_complaint_name=data.get("dispatch_complaint_name") or data.get("派遣元苦情担当者"),
            conflict_date=conflict_date,
            closing_date=data.get("closing_date") or data.get("締め日"),
            payment_date=data.get("payment_date") or data.get("支払日"),
            break_minutes=int(data.get("break_minutes", 60)),
            is_active=True
        )

    def _update_factory(self, factory: Factory, data: dict):
        """Update existing factory with new data."""
        if data.get("company_address") or data.get("派遣先住所"):
            factory.company_address = data.get("company_address") or data.get("派遣先住所")
        if data.get("plant_address") or data.get("工場住所"):
            factory.plant_address = data.get("plant_address") or data.get("工場住所")
        if data.get("conflict_date") or data.get("抵触日"):
            cd = data.get("conflict_date") or data.get("抵触日")
            if isinstance(cd, str):
                factory.conflict_date = datetime.strptime(cd, "%Y-%m-%d").date()
            elif isinstance(cd, datetime):
                factory.conflict_date = cd.date()

    # ========================================
    # EMPLOYEE IMPORT - EXCEL (Existing)
    # ========================================

    def preview_employees_excel(self, content: bytes) -> ImportResult:
        """Preview employee data from Excel file."""
        result = ImportResult()

        try:
            df = pd.read_excel(BytesIO(content), engine='openpyxl')
            result.total_rows = len(df)

            # Map Japanese column names
            column_mapping = {
                '社員№': 'employee_number',
                '社員番号': 'employee_number',
                '氏名': 'full_name_kanji',
                'カナ': 'full_name_kana',
                'ローマ字': 'full_name_romaji',
                '性別': 'gender',
                '生年月日': 'date_of_birth',
                '国籍': 'nationality',
                '住所': 'address',
                '電話番号': 'phone',
                '携帯電話': 'mobile',
                '入社日': 'hire_date',
                '退社日': 'termination_date',
                '派遣先': 'company_name',
                '工場': 'plant_name',
                '配属先': 'department',
                'ライン': 'line_name',
                '時給': 'hourly_rate',
                '単価': 'billing_rate',
                '請求単価': 'billing_rate',
                '在留資格': 'visa_type',
                'ビザ期限': 'visa_expiry_date',
                '在留カード番号': 'zairyu_card_number',
                '雇用保険': 'has_employment_insurance',
                '健康保険': 'has_health_insurance',
                '厚生年金': 'has_pension_insurance',
                '備考': 'notes',
            }

            df = df.rename(columns=column_mapping)

            for idx, row in df.iterrows():
                row_num = idx + 2
                emp_data = row.to_dict()
                emp_data = {k: (None if pd.isna(v) else v) for k, v in emp_data.items()}

                validated, errors = self._validate_employee(row_num, emp_data)
                result.errors.extend(errors)

                preview_item = {
                    "row": row_num,
                    "employee_number": emp_data.get("employee_number", ""),
                    "full_name_kanji": emp_data.get("full_name_kanji", ""),
                    "full_name_kana": emp_data.get("full_name_kana", ""),
                    "company_name": emp_data.get("company_name", ""),
                    "hourly_rate": emp_data.get("hourly_rate"),
                    "billing_rate": emp_data.get("billing_rate"),
                    "hire_date": str(emp_data.get("hire_date", "")) if emp_data.get("hire_date") else "",
                    "is_valid": len([e for e in errors if e.row == row_num]) == 0,
                    "errors": [e.message for e in errors if e.row == row_num],
                    "_raw": emp_data
                }
                result.preview_data.append(preview_item)

            result.success = len(result.errors) == 0
            result.message = f"{result.total_rows}件の従業員データを読み込みました" if result.success else f"{len(result.errors)}件のエラーがあります"

        except Exception as e:
            result.errors.append(ImportValidationError(0, "file", f"Excelエラー: {str(e)}"))
            result.message = f"Excelファイル読み込みエラー: {str(e)}"

        return result

    def import_employees(self, preview_data: List[dict], mode: str = "sync") -> ImportResult:
        """
        Import employees after preview confirmation.

        Args:
            preview_data: Validated data from preview
            mode: "create", "update", or "sync" (update existing, create new)
        """
        result = ImportResult()
        result.total_rows = len(preview_data)

        try:
            for item in preview_data:
                if not item.get("is_valid", False):
                    result.skipped_count += 1
                    continue

                raw_data = item.get("_raw", {})
                employee_number = str(raw_data.get("employee_number", "")).strip()

                if not employee_number:
                    result.skipped_count += 1
                    continue

                # Check if exists
                existing = self.db.query(Employee).filter(
                    Employee.employee_number == employee_number
                ).first()

                if existing:
                    if mode in ["update", "sync"]:
                        self._update_employee(existing, raw_data)
                        result.updated_count += 1
                    else:
                        result.skipped_count += 1
                else:
                    if mode in ["create", "sync"]:
                        employee = self._create_employee(raw_data)
                        self.db.add(employee)
                        result.imported_count += 1
                    else:
                        result.skipped_count += 1

            self.db.commit()
            result.success = True
            result.message = f"同期完了: 新規{result.imported_count}件, 更新{result.updated_count}件, スキップ{result.skipped_count}件"

        except Exception as e:
            self.db.rollback()
            result.errors.append(ImportValidationError(0, "import", f"インポートエラー: {str(e)}"))
            result.message = f"インポート失敗: {str(e)}"

        return result

    def _validate_employee(self, row: int, data: dict) -> Tuple[dict, List[ImportValidationError]]:
        """Validate a single employee record."""
        errors = []

        if not data.get("employee_number"):
            errors.append(ImportValidationError(row, "employee_number", "社員番号は必須です"))

        if not data.get("full_name_kanji"):
            errors.append(ImportValidationError(row, "full_name_kanji", "氏名は必須です"))

        if not data.get("full_name_kana"):
            errors.append(ImportValidationError(row, "full_name_kana", "カナは必須です"))

        if not data.get("hire_date"):
            errors.append(ImportValidationError(row, "hire_date", "入社日は必須です"))

        # Validate dates
        for date_field in ["hire_date", "termination_date", "date_of_birth", "visa_expiry_date"]:
            if data.get(date_field):
                try:
                    val = data[date_field]
                    if isinstance(val, str):
                        datetime.strptime(val, "%Y-%m-%d")
                except ValueError:
                    errors.append(ImportValidationError(row, date_field, f"{date_field}の日付形式が正しくありません", data[date_field]))

        return data, errors

    def _create_employee(self, data: dict) -> Employee:
        """Create new Employee from import data."""

        def parse_date(val):
            if val is None:
                return None
            if isinstance(val, date):
                return val
            if isinstance(val, datetime):
                return val.date()
            if isinstance(val, str):
                return datetime.strptime(val, "%Y-%m-%d").date()
            return None

        def parse_bool(val):
            if val is None:
                return True
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.lower() in ['true', '1', 'yes', 'はい', '○', '◯']
            return bool(val)

        def parse_decimal(val):
            if val is None:
                return None
            try:
                return Decimal(str(val))
            except:
                return None

        return Employee(
            employee_number=str(data.get("employee_number", "")).strip(),
            full_name_kanji=data.get("full_name_kanji", ""),
            full_name_kana=data.get("full_name_kana", ""),
            full_name_romaji=data.get("full_name_romaji"),
            gender=data.get("gender"),
            date_of_birth=parse_date(data.get("date_of_birth")),
            nationality=data.get("nationality", "ベトナム"),
            address=data.get("address"),
            phone=data.get("phone"),
            mobile=data.get("mobile"),
            hire_date=parse_date(data.get("hire_date")) or date.today(),
            termination_date=parse_date(data.get("termination_date")),
            company_name=data.get("company_name"),
            plant_name=data.get("plant_name"),
            department=data.get("department"),
            line_name=data.get("line_name"),
            hourly_rate=parse_decimal(data.get("hourly_rate")),
            billing_rate=parse_decimal(data.get("billing_rate")),
            visa_type=data.get("visa_type"),
            visa_expiry_date=parse_date(data.get("visa_expiry_date")),
            zairyu_card_number=data.get("zairyu_card_number"),
            has_employment_insurance=parse_bool(data.get("has_employment_insurance")),
            has_health_insurance=parse_bool(data.get("has_health_insurance")),
            has_pension_insurance=parse_bool(data.get("has_pension_insurance")),
            notes=data.get("notes"),
            status="active"
        )

    def _update_employee(self, employee: Employee, data: dict):
        """Update existing employee with new data."""

        def parse_date(val):
            if val is None:
                return None
            if isinstance(val, date):
                return val
            if isinstance(val, datetime):
                return val.date()
            if isinstance(val, str):
                return datetime.strptime(val, "%Y-%m-%d").date()
            return None

        def parse_decimal(val):
            if val is None:
                return None
            try:
                return Decimal(str(val))
            except:
                return None

        # Update fields if provided
        if data.get("full_name_kanji"):
            employee.full_name_kanji = data["full_name_kanji"]
        if data.get("full_name_kana"):
            employee.full_name_kana = data["full_name_kana"]
        if data.get("company_name"):
            employee.company_name = data["company_name"]
        if data.get("plant_name"):
            employee.plant_name = data["plant_name"]
        if data.get("department"):
            employee.department = data["department"]
        if data.get("line_name"):
            employee.line_name = data["line_name"]
        if data.get("hourly_rate"):
            employee.hourly_rate = parse_decimal(data["hourly_rate"])
        if data.get("billing_rate"):
            employee.billing_rate = parse_decimal(data["billing_rate"])
        if data.get("visa_expiry_date"):
            employee.visa_expiry_date = parse_date(data["visa_expiry_date"])
        if data.get("termination_date"):
            employee.termination_date = parse_date(data["termination_date"])
            if employee.termination_date:
                employee.status = "resigned"

    # ========================================
    # Helper Methods
    # ========================================

    def _parse_decimal(self, val: Any) -> Optional[Decimal]:
        """Parse value to Decimal."""
        if val is None:
            return None
        try:
            return Decimal(str(val))
        except:
            return None

    def _parse_int(self, val: Any) -> Optional[int]:
        """Parse value to int."""
        if val is None:
            return None
        try:
            return int(val)
        except:
            return None
