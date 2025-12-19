from .models import Quiz, Question, Option, QuizAttempt
from rest_framework import serializers # pyright: ignore[reportMissingImports]
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer  # pyright: ignore[reportMissingImports]
from django.contrib.auth.password_validation import validate_password # Important for security
from django.contrib.auth.models import User



# 1. User Serializer (To view user details)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email' , 'first_name', 'last_name')

# 2. Register Serializer (To sign up new users)
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # This creates the user and hashes the password securely
        user = User.objects.create_user(
            validated_data['username'],
            validated_data['email'],
            validated_data['password']
        )
        return user
    
# 1. Option Serializer (Simple text)
class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ('id', 'text') # We do NOT include 'is_correct' here to prevent cheating!

# 2. Question Serializer (Includes options)
class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question 
        fields = ('id', 'text', 'options')

# 3. Quiz List Serializer (For Dashboard Cards)
class QuizListSerializer(serializers.ModelSerializer):
    questions_count = serializers.IntegerField(source='questions.count', read_only=True)

    class Meta:
        model = Quiz
        fields = ('id', 'title', 'description', 'time_minutes', 'difficulty', 'questions_count')

# 4. Quiz Detail Serializer (For Taking the Quiz - includes questions)
class QuizDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ('id', 'title', 'time_minutes', 'questions')



class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        # You can even add: token['is_admin'] = user.is_staff

        return token



class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value) # Checks if password is strong enough (min length, mixed case, etc.)
        return value