from .models import Quiz, QuizAttempt,UserProfile
from .serializers import QuizListSerializer, QuizDetailSerializer,UserSerializer,RegisterSerializer,MyTokenObtainPairSerializer, ChangePasswordSerializer
from rest_framework import generics, permissions, status # pyright: ignore[reportMissingImports]
from rest_framework.response import Response # pyright: ignore[reportMissingImports]
from rest_framework.views import APIView # pyright: ignore[reportMissingImports]
from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny # pyright: ignore[reportMissingImports]
from rest_framework_simplejwt.views import TokenObtainPairView # pyright: ignore[reportMissingImports]
from django.db.models import Sum
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from rest_framework.parsers import MultiPartParser, FormParser #  pyright: ignore[reportMissingImports]

class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # This ensures a user can only edit their OWN profile
        return self.request.user
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,) # Allow anyone to register
    serializer_class = RegisterSerializer

# 1. List All Quizzes
class QuizListView(generics.ListAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizListSerializer
    permission_classes = [permissions.IsAuthenticated] # User must be logged in

# 2. Get Single Quiz Details
class QuizDetailView(generics.RetrieveAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

# 3. Submit Quiz Score
# backend/api/views.py

class SubmitQuizView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            quiz = Quiz.objects.get(pk=pk)
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND)

        # 1. Get the answers user sent: { "question_id": option_id }
        user_answers = request.data.get('answers', {}) 
        
        score = 0
        total_questions = quiz.questions.count()
        review_data = [] # We will send this back so user can review what they got wrong

        # 2. Grade the Quiz Server-Side
        for question in quiz.questions.all():
            # Get the option ID the user selected for this question
            selected_option_id = user_answers.get(str(question.id))
            
            # Find the actual correct option in DB
            correct_option = question.options.filter(is_correct=True).first()
            
            is_correct = False
            if selected_option_id and correct_option:
                # Compare IDs (Convert to string just in case)
                if str(selected_option_id) == str(correct_option.id):
                    score += 1
                    is_correct = True
            
            # 3. Prepare Review Data (Safe to send now because quiz is over)
            review_data.append({
                "question_id": question.id,
                "question_text": question.text,
                "user_selected_id": int(selected_option_id) if selected_option_id else None,
                "correct_option_id": correct_option.id if correct_option else None,
                "is_correct": is_correct,
                "options": [
                    {"id": opt.id, "text": opt.text} for opt in question.options.all()
                ]
            })

        # 4. Save the Attempt to History
        QuizAttempt.objects.create(user=request.user, quiz=quiz, score=score)

        # 5. Return Results
        return Response({
            "score": score,
            "total": total_questions,
            "percentage": (score / total_questions) * 100 if total_questions > 0 else 0,
            "review_data": review_data
        }, status=status.HTTP_200_OK)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer



# 1. Change Password View
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.data.get('old_password')):
                user.set_password(serializer.data.get('new_password'))
                user.save()
                return Response({'status': 'password set'}, status=status.HTTP_200_OK)
            return Response({'error': 'Wrong old password.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 2. Delete Account View
class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.delete()
        return Response({'status': 'account deleted'}, status=status.HTTP_200_OK)



class LeaderboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # 1. Group by User and Sum their scores
        leaders = (
            QuizAttempt.objects
            .values('user__username', 'user__first_name', 'user__last_name')
            .annotate(total_score=Sum('score'))
            .order_by('-total_score')[:10] # Top 10 only
        )

        # 2. Add Rank to the data
        data = []
        for index, entry in enumerate(leaders):
            data.append({
                "rank": index + 1,
                "username": entry['user__username'],
                "name": f"{entry['user__first_name']} {entry['user__last_name']}".strip() or entry['user__username'],
                "score": entry['total_score']
            })

        return Response(data)
    



class UserHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get all attempts for this user, newest first
        attempts = QuizAttempt.objects.filter(user=request.user).order_by('-completed_at')
        
        data = []
        for attempt in attempts:
            total_questions = attempt.quiz.questions.count()
            percentage = (attempt.score / total_questions * 100) if total_questions > 0 else 0
            
            data.append({
                "id": attempt.id,
                "quiz_title": attempt.quiz.title,
                "score": attempt.score,
                "total_questions": total_questions,
                "percentage": round(percentage),
                "date": attempt.completed_at,
                "status": "Passed" if percentage >= 60 else "Failed" # Define your passing logic here
            })
            
        return Response(data)



class UserStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        attempts = QuizAttempt.objects.filter(user=user)

        total_quizzes = attempts.count()
        
        # Calculate Average % and Passed Count manually
        total_percentage = 0
        passed_count = 0
        valid_attempts = 0

        for attempt in attempts:
            # We need the total questions to calculate percentage for this specific quiz
            question_count = attempt.quiz.questions.count()
            
            if question_count > 0:
                percentage = (attempt.score / question_count) * 100
                total_percentage += percentage
                valid_attempts += 1
                
                # Check if passed (Assuming 60% is passing)
                if percentage >= 60:
                    passed_count += 1

        avg_score = (total_percentage / valid_attempts) if valid_attempts > 0 else 0

        return Response({
            "total_quizzes": total_quizzes,
            "average_score": round(avg_score), # Returns 85 instead of 8.5
            "passed_quizzes": passed_count
        })
    



# 1. Request Password Reset Link
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny] # Anyone can ask for a reset

    def post(self, request):
        email = request.data.get('email')
        user = User.objects.filter(email=email).first()

        if user:
            # Generate Token & ID
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create the Reset Link (Point to your React App)
            reset_link = f"http://localhost:5173/reset-password?uid={uid}&token={token}"
            
            # Send Email (Prints to Console for now)
            send_mail(
                subject="Password Reset Request",
                message=f"Click the link to reset your password: {reset_link}",
                from_email="noreply@quizapp.com",
                recipient_list=[email],
                fail_silently=False,
            )
        
        # Always return 200 (Security: Don't reveal if email exists)
        return Response({"message": "If email exists, a link has been sent."}, status=status.HTTP_200_OK)

# 2. Confirm & Set New Password
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)

            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response({"message": "Password reset successful!"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"error": "Invalid link"}, status=status.HTTP_400_BAD_REQUEST)
        


class AvatarUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser) # Allow file uploads

    def get(self, request):
        # Return current avatar URL
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if profile.avatar:
            # Build full URL (e.g., http://localhost:8000/media/avatars/me.jpg)
            return Response({"avatar": request.build_absolute_uri(profile.avatar.url)})
        return Response({"avatar": "https://placehold.co/150"})

    def patch(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        file_obj = request.data.get('avatar')
        
        if file_obj:
            profile.avatar = file_obj
            profile.save()
            return Response({"message": "Avatar updated", "avatar": request.build_absolute_uri(profile.avatar.url)}, status=status.HTTP_200_OK)
        
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)



