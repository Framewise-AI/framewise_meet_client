from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage, HumanMessage
from typing import List
import os


class InMemoryHistory(BaseChatMessageHistory, BaseModel):
    """In memory implementation of chat message history."""

    messages: List[BaseMessage] = Field(default_factory=list)
    delete_list: List[BaseMessage] = Field(default_factory=list)

    class Config:
        """Configuration for this pydantic object."""
        arbitrary_types_allowed = True

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Add a list of messages to the store"""
        self.messages.extend(messages)

    def add_messages_to_delete_later(self, messages: List[BaseMessage]) -> None:
        """Add a list of messages to the store"""
        self.messages.extend(messages)
        self.delete_list.extend(messages)

    def delete_messages(self):
        self.messages = [x for x in self.messages if x not in self.delete_list]
        self.delete_list = []

    def clear(self) -> None:
        self.messages = []


class ANTLER_AGENT:
    def __init__(self,
                 session_id,
                 questions,
                 prompt_templates,
                 mcqs,
                 checkpoints=False,
                 model_name="gpt-4o-mini",
                 api_key=None):
        # API key must be provided either directly or through environment variable
        if not api_key:
            # Try to get API key from environment variable
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OpenAI API key must be provided either through the api_key parameter or OPENAI_API_KEY environment variable")

        self.model = ChatOpenAI(model=model_name, api_key=api_key)
        self.init_chain()
        self.store = {}
        self.session_id = session_id
        self.checkpoints = checkpoints
        self.prompt_templates = prompt_templates
        self.questions = questions
        self.question_index = 0
        self.introduction_done = True
        self.wrap_up = False
        self.mcqs = mcqs
        self.mcq_bool = [0]*len(self.mcqs)
        self.prepare_prompts()
        self.add_user_past_conversations()
        self.token_manager = {'completion_tokens': 0,
                              'prompt_tokens': 0, 'total_tokens': 0}

    def prepare_prompts(self):
        self.input_prompts = []
        for i, question in enumerate(self.questions):
            prompt_one_followup = self.prompt_templates['prompt_first'].format(
                question=question) if i == 0 else self.prompt_templates['prompt_next_one_followup'].format(question=question)
            prompt_two_followup = self.prompt_templates['prompt_first'].format(
                question=question) if i == 0 else self.prompt_templates['prompt_next_two_followup'].format(question=question)
            self.input_prompts.append(
                ((prompt_one_followup, prompt_one_followup), (prompt_two_followup, prompt_two_followup)))
        self.input_prompts = self.input_prompts + [((self.prompt_templates['prompt_last'], self.prompt_templates['prompt_last']),
                                                    (self.prompt_templates['prompt_last'], self.prompt_templates['prompt_last']))]

    def add_user_past_conversations(self):
        if self.session_id not in self.store:
            self.store[self.session_id] = InMemoryHistory()
        if self.question_index == -1 or self.wrap_up:
            number_of_followups = 0
        else:
            number_of_followups = 1

        if self.question_index >= len(self.questions):
            self.question_index = -1
            self.wrap_up = True
            number_of_followups = 0

        print('SYSTEM: FOLLOWUPS:', number_of_followups, self.question_index)

        system_prompt, user_prompt = self.input_prompts[self.question_index][number_of_followups-1]
        self.store[self.session_id].add_messages_to_delete_later(
            [SystemMessage(content=system_prompt)])
        self.store[self.session_id].add_messages_to_delete_later(
            [HumanMessage(content=user_prompt)])

        self.question_index = self.question_index + 1
        if self.question_index == 2:
            self.introduction_done = False
        self.conversation_counter = 0

    def init_chain(self):
        conv = [
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")]
        self.prompt = ChatPromptTemplate.from_messages(conv)
        self.chain = self.prompt | self.model

    def token_tracker(self, history):
        latest_ai_message = [
            i for i in history.messages if isinstance(i, AIMessage)]
        if len(latest_ai_message) > 0:
            increment = latest_ai_message[-1].response_metadata['token_usage']
            self.token_manager['completion_tokens'] += increment['completion_tokens']
            self.token_manager['prompt_tokens'] += increment['prompt_tokens']
            self.token_manager['total_tokens'] += increment['total_tokens']
            completion_tokens, prompt_tokens, total_tokens = str(self.token_manager['completion_tokens']), str(
                self.token_manager['prompt_tokens']), str(self.token_manager['total_tokens'])
            print('SYSTEM: LLM TOKENS:',
                  f'completion_tokens: {completion_tokens}, prompt_tokens: {prompt_tokens}, total_tokens: {total_tokens}')

    def get_session_history(self, session_id):
        self.conversation_counter += 1
        if session_id not in self.store:
            self.store[session_id] = InMemoryHistory()
        self.store[session_id] = self.memory_manager(self.store[session_id])
        history = self.store[session_id]
        return history

    def get_trailing_messages(self, history, trail=10):
        history.delete_messages()
        history.messages = history.messages[-1*trail:]
        return history

    def memory_manager(self, history):
        latest_ai_message = [
            i for i in history.messages if isinstance(i, AIMessage)]
        if len(latest_ai_message) > 0:
            latest_message = latest_ai_message[-1]
            print('SYSTEM: FULL LLM OUTPUT:', latest_message.content)
            if 'QUESTION ENDED' in latest_message.content:
                print('SYSTEM: FULL LLM OUTPUT:',
                      '------------------- QUESTION TOKEN ENCOUNTERED -----------------------')
                history = self.get_trailing_messages(history, trail=15)
                self.add_user_past_conversations()

        last_message_type_ai = isinstance(
            history.messages[-1], AIMessage) if history.messages else False
        if not self.introduction_done:
            if last_message_type_ai and self.conversation_counter >= 6 and not self.wrap_up and not self.introduction_done:
                history = self.get_trailing_messages(history, trail=15)
                self.add_user_past_conversations()
        else:
            if last_message_type_ai and self.conversation_counter >= 10 and not self.wrap_up:
                history = self.get_trailing_messages(history, trail=15)
                self.add_user_past_conversations()
        return history

    def get_llm_object(self):
        self.with_message_history = RunnableWithMessageHistory(
            self.chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="history")
        return self.with_message_history, self.session_id

    def mcq_question_tracker(self):
        if self.question_index == 0 and self.mcq_bool[2] == 0:
            self.mcq_bool[2] = 1
            return (self.mcqs[2])
        if self.question_index == 3 and self.mcq_bool[1] == 0:
            self.mcq_bool[1] = 1
            return (self.mcqs[1])
        if self.question_index == 4 and self.mcq_bool[0] == 0:
            self.mcq_bool[0] = 1
            return (self.mcqs[0])
        return ('None')


def prepare_basis_llm_v2():
    prompt_templates = {
        "prompt_first": "\n        Hi, Karan, and you are the vc analyst interviewing founder today.\n\n        Begin by introducing Antler ( in 1 line ):\n       Begin with a brief introduction question to get to know the Candidate. This will help establish context for the interview.\n\n        After the introduction, proceed with the following question:\n\n        {question}\n\n        Your main objective is to ask the Candidate the provided question and assess their response.\n\n        \n        Instructions regarding followups:\n        - Adapt your follow-up questions based on the candidate's responses. \n        - Afer the introduction question, you have a maximum of 2 questions to ask the candidate, that is question provided to you and follow-up question .\n        - Afer the candidate response to the main question, ask the follow-up question with [QUESTION ENDED] token at the end\n        \n        Instructions regarding your behaviour:\n        - You ask one question at a time and engage in a conversational manner.\n        - Be kind and empathetic throughout the interview.\n        - You keep the questions and responses concise and focused.\n        - You avoid providing or requesting programming code or technical explanations.\n        - if candidate ask you any question which is unrelated to the interview/question, ask the candidate focus on the interview process and tell the candidate its not professional to ask an interviewer about unrelated things.\n        - Do not let the candidate ask you any questions which is unrelated to the question and even if asked, keep the response very short and carryon with the interview \n\n        Strictly adhere to this.\n    ",
        "prompt_next_two_followup": "\n        Hi karan, for this interview:\n\n        The candidate has already been in conversation with you.\n    \n        Naturally, conclude the ongoing discussion from the previous conversations. And then mention transition sentences [example: 'Let's move to the next question' or Moving forward or lets shift gears a bit ]  and start asking the next question provided to you.\n        \n        Your main objective is to ask the candidate questions and assess the candidate based on the next question provided to you and **two followup questions subsequently**. Do not deviate or let the candiate deviate from your task \n        \n        Assess the candidate based on the provided question:\n\n        {question}\n        \n        Instructions regarding followups:\n        - Adapt your follow-up questions based on the candidate's responses and do not ask generic followups( Like challanges you faced etc).    \n        -IMPORTANT: You will need to ask total three questions to the candidate, including one initial question provided to you and two followups questions.     \n        - IMPORTANT: After response to the first follow-up question, regardless of the response, you will have to ask the second and final follow-up question with [QUESTION ENDED] token at the end \n      - Make sure the followup questions are not generic and are probing to test the Candidate's technical proficiency. \n  - For example, if the topic were linear regression, you should ask how they calculated gradients or what loss functions are. Make sure the topics per question still remain same but the questions are more technical.                     \n        Instructions regarding your behaviour:\n        - You ask one question at a time and engage in a conversational manner.\n        - Be kind and empathetic throughout the interview\n        - You keep the questions and responses concise and focused.\n        - You avoid providing or requesting programming code or technical explanations.\n        - if candidate ask you any question which is unrelated to the interview/question, ask the candidate focus on the interview process and tell the candidate its not professional to ask an interviewer about unrelated things.\n        - Do not let the candidate ask you any questions which is unrelated to the question and even if asked, keep the response very short and carryon with the interview \n\n        Strictly adhere to the instructions above especially regarding followups.\n    ",
        "prompt_next_one_followup": "\n        Hi karn, for this interview:\n\n        The candidate has already been in conversation with you.\n    \n        Naturally, conclude the ongoing discussion from the previous conversations. And then mention transition sentences [example: 'Let's move to the next question' or Moving forward or lets shift gears a bit ]  and start asking the next question provided to you.\n        \n        Your main objective is to ask the candidate questions and assess the candidate based on the next question provided to you and **one followup question subsequently**. Do not deviate or let the candiate deviate from your task \n        \n        Assess the candidate based on the provided question:\n\n        {question}\n\n       \n        \n        Instructions regarding followups:\n        - Adapt your follow-up question based on the candidate's responses and do not ask generic followups( Like challanges you faced etc) .        \n        -IMPORTANT: You will need to ask total two questions to the candidate, including one initial question provided to you and one followups question.     \n - IMPORTANT: After response to the question provided to you, regardless of the response, you will have to ask the ask the first and final follow-up question with [QUESTION ENDED] token at the end \n        - You can ask a maximum of two questions to the candidate, including one initial question provided to you and one followups. \n        - Make sure the followup questions are not generic and are probing to test the Candidate's technical proficiency. \n  - For example, if the topic were linear regression, you should ask how they calculated gradients or what loss functions are. Make sure the topics per question still remain same but the questions are more technical.                     \n        Instructions regarding your behaviour:\n        - You ask one question at a time and engage in a conversational manner.\n        - Be kind and empathetic throughout the interview\n        - You keep the questions and responses concise and focused.\n        - You avoid providing or requesting programming code or technical explanations.\n        - if candidate ask you any question which is unrelated to the interview/question, ask the candidate focus on the interview process and tell the candidate its not professional to ask an interviewer about unrelated things.\n        - Do not let the candidate ask you any questions which is unrelated to the question and even if asked, keep the response very short and carryon with the interview \n\n        Strictly adhere to the instructions above especially regarding followups.\n    ",
        "prompt_last": "\n        Hi, you are Karan, and you will now conclude the interview.\n\n        Thank the candidate for their insights and acknowledge the discussion about their startup.\n\n        Before wrapping up, ask if they have any final questions about the investment discussion.\n\n        Guidelines:\n        - If the candidate asks about their performance, inform them that the team will review and get back to them.\n        - If they ask about the process, mention that the team will follow up.\n        - If their question is unrelated, remind them to stay focused.\n\n        If there are no further questions, allow the candidate to conclude the meeting.\n\n        End by thanking them for their time.\n    ",
        "system_prompt_questions": ""
    }

    questions = [
        "Tell us about something you have built or created, an achievement you are proud of, or a challenge you found hard to overcome.",
        "Do you already have an idea you want to build on?",
        "How did you hear about Antler?",
        "Are you applying as a team or an individual?",
        "Where are you located, and what are your preferred areas of application?",
        "What motivates you to become an entrepreneur?",
        "What specific skills or experience do you bring to the table?"
    ]

    mcqs = [
        {
            "id": "regionsid",
            "question": "Select a region *",
            "options": [
                "Asia Pacific (APAC)",
                "Europe",
                "Americas",
                "Middle East and Africa"
            ]
        },
        {
            "id": "applyingid",
            "question": "How are you applying?",
            "options": [
                "Team",
                "Individual"
            ]
        },
        {
            "id": "hearid",
            "question": "How did you hear about Antler?",
            "options": [
                "Referral",
                "LinkedIn",
                "Press/Media",
                "Google",
                "Other"
            ]
        }
    ]
    meeting_id = 'session_1'
    api_key = "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"
    try:
        AGENT = ANTLER_AGENT(
            model_name='gpt-4o-mini',
            session_id=meeting_id,
            prompt_templates=prompt_templates,
            mcqs=mcqs,
            questions=questions,
            api_key=api_key
        )
        llm, session_id = AGENT.get_llm_object()
        return (AGENT, llm, session_id)
    except Exception as e:
        print(f"Error initializing ANTLER_AGENT: {e}")
        # Fallback to prevent the application from crashing
        return None, None, meeting_id
