import uuid

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from langchain_core.messages import HumanMessage, SystemMessage
from .graph import SYSTEM_TREKKA, app
from .models import Conversation
from .llm import llm


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = request.data.get("message")
        thread_id = request.data.get("thread_id")

        if not message:
            return Response(
                {"error": "Message required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not thread_id:
            thread_id = str(uuid.uuid4())

        state = app.get_state(
            config={"configurable": {"thread_id": thread_id}}
        )

        # Initialize state once
        if not state.values.get("initialized"):
            state.values["messages"] = [SYSTEM_TREKKA]
            state.values["initialized"] = True
            state.values["saved"] = False   # important

        state.values["messages"].append(HumanMessage(content=message))

        result = app.invoke(
            {"messages": state.values["messages"]},
            config={"configurable": {"thread_id": thread_id}}
        )

        return Response({
            "thread_id": thread_id,
            "response": result["messages"][-1].content
        })


class NewChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        thread_id = request.data.get("thread_id")
        if not thread_id:
            return Response({"ok": True})

        state = app.get_state(
            config={"configurable": {"thread_id": thread_id}}
        )

        messages = state.values.get("messages", [])

        # Only save if more than 1 message
        if len(messages) > 1:
            conversation_text = "\n".join(
                f"{msg.__class__.__name__}: {msg.content}"
                for msg in messages
                if hasattr(msg, "content")
            )

            # Generate summary
            summary = llm.invoke([
                SystemMessage(content="Summarize this conversation in 3–4 lines."),
                HumanMessage(content=conversation_text)
            ]).content.strip()

            # Generate title
            title = llm.invoke([
                SystemMessage(content="Generate a short 2–4 word title. Only the title."),
                HumanMessage(content=summary)
            ]).content.strip()
            title = " ".join(title.split()[:4])

            # Check if conversation for this thread already exists
            conv, created = Conversation.objects.update_or_create(
                user=request.user,
                id=thread_id,
                defaults={"title": title, "summary": summary}
            )

            state.values["saved"] = True  # mark as saved

        # Soft reset after saving
        state.values["messages"] = []
        state.values["initialized"] = False

        return Response({"ok": True})


class ConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = Conversation.objects.filter(
            user=request.user
        ).order_by("-created_at")

        return Response({
            "conversations": [
                {
                    "id": str(c.id),
                    "title": c.title,
                    "summary": c.summary
                }
                for c in conversations
            ]
        })


class DeleteConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        conv_id = request.data.get("id")
        if conv_id:
            Conversation.objects.filter(
                id=conv_id,
                user=request.user
            ).delete()
        return Response({"ok": True})
