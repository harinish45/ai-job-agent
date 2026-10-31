"""
Networking & Recruiter Outreach Service
Generates personalized connection requests and follow-up messages.
"""
from typing import List, Dict, Optional
import openai
from app.config import get_settings

settings = get_settings()
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

class NetworkingService:
    """Generates networking messages for job seekers."""

    def __init__(self):
        self.message_templates = {
            "linkedin_connect": self._generate_linkedin_connect,
            "recruiter_followup": self._generate_recruiter_followup,
            "referral_request": self._generate_referral_request,
            "thank_you": self._generate_thank_you,
            "interview_followup": self._generate_interview_followup,
        }

    async def generate_linkedin_connect(
        self,
        candidate_name: str,
        candidate_title: str,
        recruiter_name: str,
        recruiter_title: str,
        company: str,
        job_title: Optional[str] = None,
        shared_interest: Optional[str] = None
    ) -> str:
        """Generate a LinkedIn connection request message."""
        prompt = f"""
        Write a concise LinkedIn connection request (under 300 characters) from:

        Sender: {candidate_name}, {candidate_title}
        Recipient: {recruiter_name}, {recruiter_title} at {company}
        {f"Job of interest: {job_title}" if job_title else ""}
        {f"Shared interest: {shared_interest}" if shared_interest else ""}

        Rules:
        - Under 300 characters (LinkedIn limit)
        - Professional but personable
        - Mention specific interest in company/role
        - No generic "I'd like to add you to my network"
        - End with a soft ask or value proposition
        """

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except:
            return f"Hi {recruiter_name}, I'm {candidate_name}, a {candidate_title} interested in opportunities at {company}. Would love to connect!"

    async def generate_recruiter_followup(
        self,
        candidate_name: str,
        job_title: str,
        company: str,
        days_since_apply: int,
        key_qualification: str
    ) -> str:
        """Generate a follow-up email to a recruiter."""
        prompt = f"""
        Write a professional follow-up email to a recruiter.

        Context:
        - Candidate: {candidate_name}
        - Applied to: {job_title} at {company}
        - Days since application: {days_since_apply}
        - Key qualification: {key_qualification}

        Rules:
        - Keep to 3-4 short paragraphs
        - Reiterate enthusiasm
        - Mention one specific qualification
        - Professional but not desperate
        - Include a clear call to action
        """

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=250
            )
            return response.choices[0].message.content.strip()
        except:
            return f"""Subject: Following up on {job_title} application

Hi,

I hope this message finds you well. I wanted to follow up on my application for the {job_title} position at {company}, which I submitted {days_since_apply} days ago.

I bring strong experience in {key_qualification} and am very excited about the opportunity to contribute to your team.

Would you be available for a brief call to discuss my application? I'm happy to work around your schedule.

Best regards,
{candidate_name}"""

    async def generate_referral_request(
        self,
        candidate_name: str,
        candidate_title: str,
        contact_name: str,
        company: str,
        job_title: str,
        relationship: str  # "former_colleague", "alumni", "met_at_event"
    ) -> str:
        """Generate a referral request message."""
        prompt = f"""
        Write a polite referral request message.

        Context:
        - Requester: {candidate_name}, {candidate_title}
        - Contact: {contact_name}
        - Company: {company}
        - Job: {job_title}
        - Relationship: {relationship}

        Rules:
        - Acknowledge the relationship
        - Be specific about the ask
        - Offer to make it easy (provide resume, talking points)
        - No pressure - make it easy to say no
        - Keep it under 200 words
        """

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except:
            return f"""Hi {contact_name},

I hope you're doing well! I noticed {company} is hiring for a {job_title} role, and given my background in {candidate_title}, I think I'd be a strong fit.

Would you be open to referring me? I'd be happy to share my resume and any talking points to make it easy.

No pressure at all - I completely understand if now isn't a good time.

Thanks for considering!

{candidate_name}"""

    async def generate_thank_you(
        self,
        candidate_name: str,
        interviewer_name: str,
        company: str,
        job_title: str,
        specific_topic: Optional[str] = None
    ) -> str:
        """Generate a post-interview thank you email."""
        prompt = f"""
        Write a post-interview thank you email.

        Context:
        - Candidate: {candidate_name}
        - Interviewer: {interviewer_name}
        - Company: {company}
        - Role: {job_title}
        {f"- Specific topic discussed: {specific_topic}" if specific_topic else ""}

        Rules:
        - Send within 24 hours
        - Reference specific conversation points
        - Reiterate enthusiasm
        - Keep to 2-3 short paragraphs
        - Professional but warm
        """

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except:
            return f"""Subject: Thank you - {job_title} interview

Hi {interviewer_name},

Thank you for taking the time to speak with me about the {job_title} role at {company} today. I really enjoyed learning more about the team and the exciting challenges you're tackling.

{f"I particularly enjoyed our discussion about {specific_topic}." if specific_topic else "I'm very excited about the opportunity to contribute to your team."}

Please don't hesitate to reach out if you need any additional information. I look forward to hearing from you.

Best,
{candidate_name}"""

    async def generate_interview_followup(
        self,
        candidate_name: str,
        interviewer_name: str,
        company: str,
        job_title: str,
        days_since_interview: int,
        additional_info: Optional[str] = None
    ) -> str:
        """Generate a follow-up after interview with no response."""
        prompt = f"""
        Write a follow-up email after an interview with no response.

        Context:
        - Candidate: {candidate_name}
        - Interviewer: {interviewer_name}
        - Company: {company}
        - Role: {job_title}
        - Days since interview: {days_since_interview}
        {f"- Additional info to share: {additional_info}" if additional_info else ""}

        Rules:
        - Polite and professional
        - Reference the interview
        - {f"Include the additional information" if additional_info else "Reiterate interest"}
        - Not pushy - acknowledge they may be busy
        - Keep to 2 paragraphs
        """

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except:
            return f"""Subject: Following up on {job_title}

Hi {interviewer_name},

I hope you're doing well. I wanted to follow up regarding the {job_title} role at {company}, following our interview {days_since_interview} days ago.

{f"I wanted to share {additional_info}. " if additional_info else ""}I'm still very interested in the opportunity and would welcome any updates on the hiring timeline.

Thank you for your time and consideration.

Best,
{candidate_name}"""

    def _generate_linkedin_connect(self, **kwargs):
        return self.generate_linkedin_connect(**kwargs)

    def _generate_recruiter_followup(self, **kwargs):
        return self.generate_recruiter_followup(**kwargs)

    def _generate_referral_request(self, **kwargs):
        return self.generate_referral_request(**kwargs)

    def _generate_thank_you(self, **kwargs):
        return self.generate_thank_you(**kwargs)

    def _generate_interview_followup(self, **kwargs):
        return self.generate_interview_followup(**kwargs)
