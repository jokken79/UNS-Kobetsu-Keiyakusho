/**
 * TypeScript type definitions for UNS Kobetsu Keiyakusho
 */

// Contact Info
export interface ContactInfo {
  department: string
  position: string
  name: string
  phone: string
}

// Manager Info
export interface ManagerInfo {
  department: string
  position: string
  name: string
  phone: string
  license_number?: string
}

// Kobetsu Keiyakusho Create
export interface KobetsuCreate {
  factory_id: number
  dispatch_assignment_id?: number
  employee_ids: number[]
  contract_date: string
  dispatch_start_date: string
  dispatch_end_date: string
  work_content: string
  responsibility_level: string
  worksite_name: string
  worksite_address: string
  organizational_unit?: string
  supervisor_department: string
  supervisor_position: string
  supervisor_name: string
  work_days: string[]
  work_start_time: string
  work_end_time: string
  break_time_minutes: number
  overtime_max_hours_day?: number
  overtime_max_hours_month?: number
  overtime_max_days_month?: number
  holiday_work_max_days?: number
  safety_measures?: string
  haken_moto_complaint_contact: ContactInfo
  haken_saki_complaint_contact: ContactInfo
  hourly_rate: number
  overtime_rate: number
  night_shift_rate?: number
  holiday_rate?: number
  welfare_facilities?: string[]
  haken_moto_manager: ManagerInfo
  haken_saki_manager: ManagerInfo
  termination_measures?: string
  is_kyotei_taisho?: boolean
  is_direct_hire_prevention?: boolean
  is_mukeiko_60over_only?: boolean
  notes?: string
}

// Kobetsu Keiyakusho Update
export interface KobetsuUpdate {
  contract_date?: string
  dispatch_end_date?: string
  work_content?: string
  responsibility_level?: string
  supervisor_name?: string
  work_days?: string[]
  hourly_rate?: number
  overtime_rate?: number
  status?: string
  notes?: string
}

// Kobetsu Keiyakusho Response
export interface KobetsuResponse {
  id: number
  factory_id: number
  dispatch_assignment_id?: number
  contract_number: string
  contract_date: string
  dispatch_start_date: string
  dispatch_end_date: string
  work_content: string
  responsibility_level: string
  worksite_name: string
  worksite_address: string
  organizational_unit?: string
  supervisor_department: string
  supervisor_position: string
  supervisor_name: string
  work_days: string[]
  work_start_time: string
  work_end_time: string
  break_time_minutes: number
  overtime_max_hours_day?: number
  overtime_max_hours_month?: number
  overtime_max_days_month?: number
  holiday_work_max_days?: number
  safety_measures?: string
  haken_moto_complaint_contact: ContactInfo
  haken_saki_complaint_contact: ContactInfo
  hourly_rate: number
  overtime_rate: number
  night_shift_rate?: number
  holiday_rate?: number
  welfare_facilities?: string[]
  haken_moto_manager: ManagerInfo
  haken_saki_manager: ManagerInfo
  termination_measures?: string
  is_kyotei_taisho: boolean
  is_direct_hire_prevention: boolean
  is_mukeiko_60over_only: boolean
  number_of_workers: number
  status: string
  pdf_path?: string
  signed_date?: string
  notes?: string
  created_at: string
  updated_at: string
  created_by?: number
  employees?: EmployeeBasic[]
}

// Kobetsu List Item
export interface KobetsuListItem {
  id: number
  contract_number: string
  worksite_name: string
  dispatch_start_date: string
  dispatch_end_date: string
  number_of_workers: number
  status: string
  created_at: string
}

// Kobetsu Stats
export interface KobetsuStats {
  total_contracts: number
  active_contracts: number
  expiring_soon: number
  expired_contracts: number
  draft_contracts: number
  total_workers: number
}

// Employee Basic
export interface EmployeeBasic {
  id: number
  employee_id: string
  full_name_roman: string
  nationality?: string
}

// Paginated Response
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
  has_more: boolean
}

// Auth Types
export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface User {
  id: number
  email: string
  full_name: string
  role: string
  is_active: boolean
}

// API List Params
export interface KobetsuListParams {
  skip?: number
  limit?: number
  status?: string
  factory_id?: number
  search?: string
  start_date?: string
  end_date?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}
