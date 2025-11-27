"""
Template Model
Customizable document templates for contracts.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DocumentTemplate(Base):
    """
    Customizable document templates for generating contracts.
    Allows different clients/factories to have personalized formats.
    """
    __tablename__ = "document_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Template details
    name = Column(String(255), nullable=False)
    template_type = Column(String(50), nullable=False, index=True)
    # Types: 'kobetsu_keiyakusho', 'hakenmoto_daicho', 'hakensaki_daicho', 'shugyo_joken'

    # Scope
    is_default = Column(Boolean, default=False, index=True)
    factory_id = Column(Integer, ForeignKey("factories.id"), nullable=True, index=True)
    # If factory_id is NULL, it's a global template
    # If factory_id is set, it's specific to that factory

    # Template content
    header_template = Column(Text)  # Header HTML/text with variables
    body_template = Column(Text, nullable=False)  # Main body with variables
    footer_template = Column(Text)  # Footer HTML/text with variables

    # Styling
    css_styles = Column(Text)  # Custom CSS
    logo_url = Column(String(500))  # Custom logo path
    font_family = Column(String(100), default="MS Gothic")

    # Variables (for documentation)
    available_variables = Column(JSON)
    # Example: {"contract_number": "契約番号", "factory_name": "派遣先名称", ...}

    # Conditional blocks
    conditional_sections = Column(JSON)
    # Example: {"show_safety_clause": "if contract.safety_measures is not None"}

    # Status
    is_active = Column(Boolean, default=True, index=True)
    version = Column(String(20), default="1.0")

    # Metadata
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_used_at = Column(DateTime)

    # Relationships
    factory = relationship("Factory", backref="custom_templates")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        scope = f"factory:{self.factory_id}" if self.factory_id else "global"
        return f"<DocumentTemplate {self.name} ({scope})>"


class TemplateVariable(Base):
    """
    Custom variables that can be used in templates.
    Allows users to define custom fields beyond the standard 16 items.
    """
    __tablename__ = "template_variables"

    id = Column(Integer, primary_key=True, index=True)

    template_id = Column(Integer, ForeignKey("document_templates.id"), nullable=False, index=True)

    # Variable definition
    variable_name = Column(String(100), nullable=False)  # e.g., "custom_clause_1"
    display_name = Column(String(255), nullable=False)  # e.g., "追加条項1"
    data_type = Column(String(20), default="text")  # 'text', 'number', 'date', 'boolean'

    # Default value
    default_value = Column(Text)

    # Validation
    is_required = Column(Boolean, default=False)
    validation_regex = Column(String(500))
    min_length = Column(Integer)
    max_length = Column(Integer)

    # Metadata
    description = Column(Text)
    display_order = Column(Integer, default=0)

    # Relationships
    template = relationship("DocumentTemplate", backref="custom_variables")

    def __repr__(self):
        return f"<TemplateVariable {self.variable_name} for template:{self.template_id}>"
