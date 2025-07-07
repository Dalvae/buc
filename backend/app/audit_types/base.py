# app/audit_types/base.py

from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

from fastapi import HTTPException

from app.models import QuestionTemplate, AuditResponse, QuestionType, Answer, AssignedQuestion

class AuditTypeDefinitionBase(ABC):
    @abstractmethod
    def get_key(self) -> str:
        """Return the unique string key for this audit type."""
        raise NotImplementedError

    @abstractmethod
    def get_name(self) -> str:
        """Return a human-readable name for this audit type."""
        raise NotImplementedError

    def get_default_sections(self) -> List[Dict[str, Any]]:
        """Return a list of default section definitions, if any."""
        return []

    def get_default_questions(self) -> List[Dict[str, Any]]:
        """Return a list of default question definitions to be created with a new template."""
        return []

    @abstractmethod
    def get_allowed_question_types(self) -> List[QuestionType]: # Reverted type hint
        """Return a list of QuestionType enum values valid for this audit type."""
        raise NotImplementedError

    @abstractmethod
    def validate_question(self, question_template: QuestionTemplate) -> None: # Reverted type hint
        """
        Validate a question against the audit type's rules.
        Raise ValueError if invalid.
        """
        if question_template.question_type not in self.get_allowed_question_types():
            raise ValueError(
                f"Question type '{question_template.question_type}' is not allowed for "
                f"'{self.get_name()}' audits. Allowed types are: {self.get_allowed_question_types()}"
            )
        if question_template.question_type in [QuestionType.MULTIPLE_CHOICE_SINGLE, QuestionType.MULTIPLE_CHOICE_MULTIPLE]:
            if not isinstance(question_template.options, list) or not question_template.options:
                raise ValueError("Multiple choice questions must have a non-empty list of options.")

    @abstractmethod
    def calculate_score(self, audit_response: AuditResponse) -> float | None: # Reverted type hint
        """
        Calculate the score for a completed audit.
        Return a float score or None if not applicable.
        """
        raise NotImplementedError

    def validate_answer(
        self, answer: Answer, assigned_question: AssignedQuestion
    ) -> None:
        if assigned_question.question_type == QuestionType.RATING_SCALE:
            if answer.answer_value is not None and not isinstance(
                answer.answer_value, int | float
            ):
                raise HTTPException(status_code=400, detail="Answer for rating scale must be a number.")

            options = assigned_question.options
            if isinstance(options, dict):
                min_val = options.get("min")
                max_val = options.get("max")

                if min_val is not None and max_val is not None and answer.answer_value is not None:
                    try:
                        min_val_float = float(min_val)
                        max_val_float = float(max_val)
                        answer_value_float = float(answer.answer_value)
                        if not (min_val_float <= answer_value_float <= max_val_float):
                            raise HTTPException(
                                status_code=400, detail=f"Answer for rating scale must be between {min_val} and {max_val}."
                            )
                    except (ValueError, TypeError):
                        raise HTTPException(status_code=400, detail="Invalid values in rating scale options.")
        elif assigned_question.question_type == QuestionType.TEXT:
            if not isinstance(answer.answer_value, str) and answer.answer_value is not None:
                raise HTTPException(status_code=400, detail="Answer for text question must be a string or null.")
