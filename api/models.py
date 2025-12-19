from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# -------------------------------------------------
# 1. Quiz Model (Category / Topic)
# -------------------------------------------------
class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Time limit for the quiz (in minutes)
    time_minutes = models.IntegerField(default=10)

    # Difficulty level
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='Medium'
    )

    # Icon name (for frontend usage)
    icon_name = models.CharField(
        max_length=50,
        default='FaQuestionCircle'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# -------------------------------------------------
# 2. Question Model
# -------------------------------------------------
class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        related_name='questions',
        on_delete=models.CASCADE
    )
    text = models.TextField()

    def __str__(self):
        return f"{self.quiz.title} - {self.text[:50]}"


# -------------------------------------------------
# 3. Option Model (Answer Choices)
# -------------------------------------------------
class Option(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['question'],
                condition=models.Q(is_correct=True),
                name='one_correct_option_per_question'
            )
        ]



# -------------------------------------------------
# 4. Quiz Attempt Model (User History / Score)
# -------------------------------------------------
class QuizAttempt(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE
    )
    score = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} | {self.quiz.title} | Score: {self.score}"



# 1. Create the Profile Model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# 2. Auto-create Profile when User is created (Signal)
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()