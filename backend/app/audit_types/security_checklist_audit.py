from typing import Any, List, Dict

from fastapi import HTTPException

from app.models import QuestionTemplate, AuditResponse, QuestionType, Answer, AssignedQuestion
from app.audit_types.base import AuditTypeDefinitionBase


class SecurityChecklistAuditType(AuditTypeDefinitionBase):
    def get_key(self) -> str:
        return "SECURITY_CHECKLIST_AUDIT"

    def get_name(self) -> str:
        return "Security Checklist Audit"

    def get_default_sections(self) -> List[Dict[str, str]]:
        return [
            {"id": "physical_security", "name": "Physical Security"},
            {"id": "access_control", "name": "Access Control"},
            {"id": "data_security", "name": "Data Security"},
        ]

    def get_allowed_question_types(self) -> List[QuestionType]:
        return [QuestionType.YES_NO, QuestionType.TEXT]

    def get_default_questions(self) -> List[Dict[str, Any]]:
        return [
            {
                "text": "Are all external doors and windows securely locked?",
                "question_type": QuestionType.YES_NO,
                "options": {},
                "order": 1,
                "is_mandatory": True,
                "section_id": "physical_security",
                "scoring_weight": 1.0,
            },
            {
                "text": "Is the alarm system armed and functional?",
                "question_type": QuestionType.YES_NO,
                "options": {},
                "order": 2,
                "is_mandatory": True,
                "section_id": "physical_security",
                "scoring_weight": 1.0,
            },
            {
                "text": "Are visitor logs properly maintained and reviewed?",
                "question_type": QuestionType.YES_NO,
                "options": {},
                "order": 3,
                "is_mandatory": True,
                "section_id": "access_control",
                "scoring_weight": 1.0,
            },
            {
                "text": "Are all user accounts regularly reviewed for necessity and privilege?",
                "question_type": QuestionType.YES_NO,
                "options": {},
                "order": 4,
                "is_mandatory": True,
                "section_id": "data_security",
                "scoring_weight": 1.0,
            },
            {
                "text": "Comments on overall security posture:",
                "question_type": QuestionType.TEXT,
                "options": {},
                "order": 5,
                "is_mandatory": False,
                "section_id": None,
                "scoring_weight": 0.0,
            },
        ]

    def validate_question(self, question_template: QuestionTemplate) -> None:
        if question_template.question_type not in self.get_allowed_question_types():
            raise ValueError(
                f"Question type {question_template.question_type} not allowed for Security Checklist Audit."
            )
        if question_template.question_type == QuestionType.YES_NO:
            if question_template.options: # YES_NO questions should not have options
                raise ValueError("YES_NO questions should not have options defined.")

    def calculate_score(self, audit_response: AuditResponse) -> float:
        total_possible_score = 0.0
        achieved_score = 0.0

        for answer in audit_response.answers:
            assigned_question = answer.assigned_question
            if assigned_question.question_type == QuestionType.YES_NO:
                weight = assigned_question.scoring_weight
                if weight is not None:
                    total_possible_score += weight
                    if answer.answer_value is True:
                        achieved_score += weight
        
        if total_possible_score == 0:
            return 0.0
        
        return (achieved_score / total_possible_score) * 100

    def validate_answer(self, answer: Answer, assigned_question: AssignedQuestion) -> None:
        if assigned_question.question_type == QuestionType.YES_NO:
            if not isinstance(answer.answer_value, bool) and answer.answer_value is not None:
                raise HTTPException(status_code=400, detail="Answer for YES_NO must be a boolean or null.")
        elif assigned_question.question_type == QuestionType.TEXT:
            if not isinstance(answer.answer_value, str) and answer.answer_value is not None:
                raise HTTPException(status_code=400, detail="Answer for text question must be a string or null.")
