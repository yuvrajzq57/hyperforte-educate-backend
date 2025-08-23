from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import Course, Module, Section, Quiz, Question, QuestionOption
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Load test data for courses app'

    def handle(self, *args, **options):
        # Create an instructor if not exists
        instructor, created = User.objects.get_or_create(
            username='instructor',
            defaults={
                'email': 'instructor@example.com',
                'is_staff': True,
                'is_superuser': False
            }
        )
        if created:
            instructor.set_password('instructor123')
            instructor.save()
            self.stdout.write(self.style.SUCCESS('Created instructor user'))

        # Create a test course
        course, created = Course.objects.get_or_create(
            title='Introduction to Python Programming',
            defaults={
                'subtitle': 'Learn Python from scratch',
                'description': 'A comprehensive introduction to Python programming language',
                'learning_outcomes': 'Understand Python syntax, data structures, and basic programming concepts',
                'level': 'beginner',
                'status': 'published',
                'language': 'English',
                'price': 49.99,
                'is_free': False,
                'estimated_duration': 360,  # 6 hours
                'instructor': instructor,
                'average_rating': 4.5,
                'total_reviews': 10,
                'is_featured': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created course: {course.title}'))

            # Create modules
            modules_data = [
                {
                    'title': 'Getting Started with Python',
                    'description': 'Introduction to Python and setting up your development environment',
                    'order_number': 1,
                    'is_free': True,
                    'estimated_duration': 60
                },
                {
                    'title': 'Python Basics',
                    'description': 'Learn the fundamentals of Python programming',
                    'order_number': 2,
                    'is_free': False,
                    'estimated_duration': 120
                },
                {
                    'title': 'Control Flow and Functions',
                    'description': 'Learn about loops, conditionals, and functions',
                    'order_number': 3,
                    'is_free': False,
                    'estimated_duration': 180
                }
            ]

            for module_data in modules_data:
                module = Module.objects.create(course=course, **module_data)
                self.stdout.write(self.style.SUCCESS(f'  - Created module: {module.title}'))

                # Create sections for the first module
                if module.order_number == 1:
                    sections_data = [
                        {
                            'title': 'Introduction to Python',
                            'content': 'What is Python and why learn it?',
                            'content_type': 'text',
                            'order_number': 1,
                            'is_free': True
                        },
                        {
                            'title': 'Installing Python',
                            'content': 'Step-by-step guide to install Python',
                            'content_type': 'text',
                            'order_number': 2,
                            'is_free': True
                        },
                        {
                            'title': 'Your First Python Program',
                            'content': 'Write and run your first Python program',
                            'content_type': 'text',
                            'order_number': 3,
                            'is_free': True
                        }
                    ]

                    for section_data in sections_data:
                        section = Section.objects.create(module=module, **section_data)
                        self.stdout.write(self.style.SUCCESS(f'    - Created section: {section.title}'))

            # Create a quiz for the first module
            quiz = Quiz.objects.create(
                module=module,
                title='Module 1 Quiz',
                description='Test your knowledge of Python basics',
                passing_score=70,
                time_limit=30,
                max_attempts=3,
                show_correct_answers=True,
                require_passing=True
            )
            self.stdout.write(self.style.SUCCESS(f'  - Created quiz: {quiz.title}'))

            # Add questions to the quiz
            questions_data = [
                {
                    'question_text': 'What is the correct extension for Python files?',
                    'question_type': 'single_choice',
                    'explanation': 'Python files use the .py extension',
                    'points': 1,
                    'order_number': 1,
                    'options': [
                        {'option_text': '.python', 'is_correct': False, 'order_number': 1},
                        {'option_text': '.py', 'is_correct': True, 'order_number': 2},
                        {'option_text': '.pt', 'is_correct': False, 'order_number': 3},
                        {'option_text': '.pyth', 'is_correct': False, 'order_number': 4},
                    ]
                },
                {
                    'question_text': 'Which of the following are Python data types?',
                    'question_type': 'multiple_choice',
                    'explanation': 'Python has several built-in data types including integers, strings, and lists',
                    'points': 2,
                    'order_number': 2,
                    'options': [
                        {'option_text': 'int', 'is_correct': True, 'order_number': 1},
                        {'option_text': 'string', 'is_correct': True, 'order_number': 2},
                        {'option_text': 'list', 'is_correct': True, 'order_number': 3},
                        {'option_text': 'char', 'is_correct': False, 'order_number': 4},
                    ]
                }
            ]

            for q_data in questions_data:
                options = q_data.pop('options')
                question = Question.objects.create(quiz=quiz, **q_data)
                self.stdout.write(self.style.SUCCESS(f'    - Created question: {question.question_text[:50]}...'))
                
                for opt_data in options:
                    QuestionOption.objects.create(question=question, **opt_data)

            self.stdout.write(self.style.SUCCESS('Successfully loaded test data!'))
        else:
            self.stdout.write(self.style.WARNING('Test data already exists. Skipping...'))
