from typing import Any, List, Dict, Optional

from fastapi import HTTPException

from app.models import QuestionTemplate, AuditResponse, QuestionType, Answer, AssignedQuestion
from app.audit_types.base import AuditTypeDefinitionBase


class FiveSAuditType(AuditTypeDefinitionBase):
    def get_key(self) -> str:
        return "FIVE_S_AUDIT"

    def get_name(self) -> str:
        return "5S Audit"

    def get_default_sections(self) -> List[Dict[str, str]]:
        return [
            {"id": "sort", "name": "Sort (Seiri)"},
            {"id": "set_in_order", "name": "Set in Order (Seiton)"},
            {"id": "shine", "name": "Shine (Seiso)"},
            {"id": "standardize", "name": "Standardize (Seiketsu)"},
            {"id": "sustain", "name": "Sustain (Shitsuke)"},
        ]

    def get_allowed_question_types(self) -> List[QuestionType]:
        return [QuestionType.RATING_SCALE, QuestionType.TEXT]

    def get_default_questions(self) -> List[Dict[str, Any]]:
        return [
            {
                "text": "Are unnecessary items removed from the workplace?",
                "question_type": QuestionType.RATING_SCALE,
                "options": {"min": 1, "max": 5, "step": 1},
                "order": 1,
                "is_mandatory": True,
                "section_id": "sort",
                "scoring_weight": 1.0,
            },
            {
                "text": "Are all items in their designated places and clearly labeled?",
                "question_type": QuestionType.RATING_SCALE,
                "options": {"min": 1, "max": 5, "step": 1},
                "order": 2,
                "is_mandatory": True,
                "section_id": "set_in_order",
                "scoring_weight": 1.0,
            },
            {
                "text": "Is the workplace clean and free of dirt and debris?",
                "question_type": QuestionType.RATING_SCALE,
                "options": {"min": 1, "max": 5, "step": 1},
                "order": 3,
                "is_mandatory": True,
                "section_id": "shine",
                "scoring_weight": 1.0,
            },
            {
                "text": "Are standards for cleanliness and organization established and followed?",
                "question_type": QuestionType.RATING_SCALE,
                "options": {"min": 1, "max": 5, "step": 1},
                "order": 4,
                "is_mandatory": True,
                "section_id": "standardize",
                "scoring_weight": 1.0,
            },
            {
                "text": "Are 5S principles regularly reviewed and improved upon?",
                "question_type": QuestionType.RATING_SCALE,
                "options": {"min": 1, "max": 5, "step": 1},
                "order": 5,
                "is_mandatory": True,
                "section_id": "sustain",
                "scoring_weight": 1.0,
            },
            {
                "text": "General comments on 5S implementation:",
                "question_type": QuestionType.TEXT,
                "options": {},
                "order": 6,
                "is_mandatory": False,
                "section_id": None,
                "scoring_weight": 0.0,
            },
        ]

    def validate_question(self, question_template: QuestionTemplate) -> None:
        if question_template.question_type not in self.get_allowed_question_types():
            raise ValueError(
                f"Question type {question_template.question_type} not allowed for 5S Audit."
            )
        if question_template.question_type == QuestionType.RATING_SCALE:
            options = question_template.options
            if not isinstance(options, dict) or "min" not in options or "max" not in options:
                raise ValueError("Rating scale questions must define 'min' and 'max' in options.")
            if not isinstance(options["min"], int | float) or not isinstance(
                options["max"], int | float
            ):
                raise ValueError("Rating scale 'min' and 'max' must be numeric.")
            if options["min"] >= options["max"]:
                raise ValueError("Rating scale 'min' must be less than 'max'.")

    def calculate_score(self, audit_response: AuditResponse) -> float:
        total_score = 0.0
        max_possible_score = 0.0

        for answer in audit_response.answers:
            assigned_question = answer.assigned_question
            if assigned_question.question_type == QuestionType.RATING_SCALE:
                weight = assigned_question.scoring_weight
                if weight is None or not isinstance(assigned_question.options, dict):
                    continue

                max_val = assigned_question.options.get("max")
                if max_val is None:
                    continue
                
                try:
                    max_possible_score += float(max_val) * weight
                except (ValueError, TypeError):
                    continue

                if answer.answer_value is not None:
                    try:
                        score_value = float(answer.answer_value)
                        total_score += score_value * weight
                    except (ValueError, TypeError):
                        continue

        if max_possible_score == 0:
            return 0.0

        return (total_score / max_possible_score) * 100

    def validate_answer(self, answer: Answer, assigned_question: AssignedQuestion) -> None:
        if assigned_question.question_type == QuestionType.RATING_SCALE:
            if answer.answer_value is not None:
                if not isinstance(answer.answer_value, int | float):
                    raise HTTPException(status_code=400, detail="Answer for rating scale must be a number.")
                
                if isinstance(assigned_question.options, dict):
                    min_val = assigned_question.options.get("min")
                    max_val = assigned_question.options.get("max")
                    if min_val is not None and max_val is not None:
                        try:
                            if not (float(min_val) <= float(answer.answer_value) <= float(max_val)):
                                raise HTTPException(status_code=400, detail=f"Answer for rating scale must be between {min_val} and {max_val}.")
                        except (ValueError, TypeError):
                            raise HTTPException(status_code=400, detail="Invalid min/max values in question options.")
        elif assigned_question.question_type == QuestionType.TEXT:
            if not isinstance(answer.answer_value, str) and answer.answer_value is not None:
                raise HTTPException(status_code=400, detail="Answer for text question must be a string or null.")
