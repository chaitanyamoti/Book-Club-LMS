from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
from core.models import (
    UserProfile, Book, Transaction, ReadingLog,
    BookRequest, ClubSettings
)


class Command(BaseCommand):
    help = 'Populate the database with sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')

        # Create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@bookclub.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            UserProfile.objects.get_or_create(
                user=admin_user,
                defaults={'role': 'ADMIN'}
            )
            self.stdout.write('Created admin user: admin@bookclub.com / admin123')

        # Create member users
        member_names = [
            ('john', 'john@example.com', 'John', 'Doe'),
            ('jane', 'jane@example.com', 'Jane', 'Smith'),
            ('bob', 'bob@example.com', 'Bob', 'Johnson'),
            ('alice', 'alice@example.com', 'Alice', 'Williams'),
            ('charlie', 'charlie@example.com', 'Charlie', 'Brown'),
            ('diana', 'diana@example.com', 'Diana', 'Davis'),
            ('eve', 'eve@example.com', 'Eve', 'Miller'),
            ('frank', 'frank@example.com', 'Frank', 'Wilson'),
            ('grace', 'grace@example.com', 'Grace', 'Moore'),
            ('henry', 'henry@example.com', 'Henry', 'Taylor')
        ]

        members = []
        for username, email, first_name, last_name in member_names:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                profile, _ = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'role': 'MEMBER'}
                )
                # Add some reading streaks
                profile.streak_days = random.randint(0, 30)
                profile.longest_streak = max(profile.streak_days, random.randint(10, 50))
                profile.last_reading_date = timezone.now().date() - timedelta(days=random.randint(0, 7))
                profile.save()
                members.append(user)

        self.stdout.write(f'Created {len(members)} member users')

        # Create sample books
        books_data = [
            ('The Great Gatsby', 'F. Scott Fitzgerald', '978-0-7432-7356-5', 'Fiction', 'A classic American novel about the Jazz Age.'),
            ('To Kill a Mockingbird', 'Harper Lee', '978-0-06-112008-4', 'Fiction', 'A gripping tale of racial injustice and childhood innocence.'),
            ('1984', 'George Orwell', '978-0-452-28423-4', 'Dystopian', 'A dystopian social science fiction novel.'),
            ('Pride and Prejudice', 'Jane Austen', '978-0-14-143951-8', 'Romance', 'A romantic novel of manners.'),
            ('The Catcher in the Rye', 'J.D. Salinger', '978-0-316-76948-0', 'Fiction', 'A controversial novel about teenage rebellion.'),
            ('Harry Potter and the Philosopher\'s Stone', 'J.K. Rowling', '978-0-7475-3269-9', 'Fantasy', 'The first book in the Harry Potter series.'),
            ('The Lord of the Rings', 'J.R.R. Tolkien', '978-0-544-00003-7', 'Fantasy', 'An epic high-fantasy novel.'),
            ('Dune', 'Frank Herbert', '978-0-441-17271-9', 'Science Fiction', 'A science fiction epic.'),
            ('The Hitchhiker\'s Guide to the Galaxy', 'Douglas Adams', '978-0-345-39180-3', 'Science Fiction', 'A comedic science fiction series.'),
            ('Neuromancer', 'William Gibson', '978-0-441-56956-4', 'Science Fiction', 'A groundbreaking cyberpunk novel.'),
            ('The Name of the Wind', 'Patrick Rothfuss', '978-0-7564-0407-9', 'Fantasy', 'An epic fantasy novel.'),
            ('American Gods', 'Neil Gaiman', '978-0-380-97365-1', 'Fantasy', 'A blend of Americana, fantasy, and mythology.'),
            ('The Martian', 'Andy Weir', '978-0-553-41802-6', 'Science Fiction', 'A survival story on Mars.'),
            ('Ready Player One', 'Ernest Cline', '978-0-307-98478-6', 'Science Fiction', 'A dystopian adventure in a virtual reality world.'),
            ('The Night Circus', 'Erin Morgenstern', '978-0-385-35039-2', 'Fantasy', 'A magical competition between two young illusionists.'),
            ('Good Omens', 'Neil Gaiman & Terry Pratchett', '978-0-06-085398-3', 'Fantasy', 'A comedic take on the apocalypse.'),
            ('The Ocean at the End of the Lane', 'Neil Gaiman', '978-0-06-225565-5', 'Fantasy', 'A dark fantasy tale of childhood and magic.'),
            ('Station Eleven', 'Emily St. John Mandel', '978-0-385-35341-6', 'Science Fiction', 'A post-apocalyptic novel about art and humanity.'),
            ('The Three-Body Problem', 'Liu Cixin', '978-7-5366-9293-0', 'Science Fiction', 'A hard science fiction novel from China.'),
            ('Circe', 'Madeline Miller', '978-0-316-36999-4', 'Fantasy', 'A retelling of the story of Circe from Greek mythology.'),
            ('The Priory of the Orange Tree', 'Samantha Shannon', '978-1-5266-0107-2', 'Fantasy', 'An epic standalone fantasy novel.'),
            ('The Invisible Life of Addie LaRue', 'V.E. Schwab', '978-0-7653-8470-8', 'Fantasy', 'A deal with the devil for immortality.'),
            ('Project Hail Mary', 'Andy Weir', '978-0-593-13505-4', 'Science Fiction', 'A lone astronaut on a mission to save humanity.'),
            ('The Seven Husbands of Evelyn Hugo', 'Taylor Jenkins Reid', '978-1-5011-3467-2', 'Fiction', 'A reclusive Hollywood icon tells her life story.'),
            ('Klara and the Sun', 'Kazuo Ishiguro', '978-0-571-36938-3', 'Science Fiction', 'An Artificial Friend observes human behavior.'),
            ('The Midnight Library', 'Matt Haig', '978-0-525-55947-4', 'Fiction', 'A library between life and death.'),
            ('Shuggie Bain', 'Douglas Stuart', '978-1-5290-4637-7', 'Fiction', 'A coming-of-age story set in 1980s Glasgow.'),
            ('Such a Fun Age', 'Kiley Reid', '978-0-525-57384-6', 'Fiction', 'A story exploring race and privilege.'),
            ('The Vanishing Half', 'Brit Bennett', '978-0-525-53629-1', 'Fiction', 'Twin sisters who choose to live in two very different worlds.'),
            ('Transcendent Kingdom', 'Yaa Gyasi', '978-0-525-57613-9', 'Fiction', 'A Ghanaian family in Alabama, neuroscience, and faith.')
        ]

        books = []
        genres = ['Fiction', 'Fantasy', 'Science Fiction', 'Romance', 'Dystopian', 'Mystery', 'Thriller', 'Historical Fiction', 'Biography', 'Self-Help']

        for title, author, isbn, genre, description in books_data:
            book, created = Book.objects.get_or_create(
                title=title,
                author=author,
                defaults={
                    'isbn': isbn,
                    'genre': genre or random.choice(genres),
                    'description': description,
                    'total_copies': random.randint(1, 5),
                    'available_copies': random.randint(0, 3),
                    'added_by': admin_user
                }
            )
            if created:
                books.append(book)

        self.stdout.write(f'Created {len(books)} sample books')

        # Create transactions
        transactions = []
        for _ in range(15):
            book = random.choice(books)
            user = random.choice(members)

            # Check if user already has this book
            existing = Transaction.objects.filter(
                book=book,
                user=user,
                return_date__isnull=True
            ).exists()

            if not existing and book.available_copies > 0:
                issue_date = timezone.now() - timedelta(days=random.randint(0, 60))
                due_date = issue_date + timedelta(days=30)

                # Some transactions are returned, some are still active
                is_returned = random.choice([True, False])
                return_date = None
                if is_returned:
                    return_date = issue_date + timedelta(days=random.randint(1, 45))

                transaction = Transaction.objects.create(
                    book=book,
                    user=user,
                    transaction_type='ISSUE',
                    issue_date=issue_date,
                    due_date=due_date,
                    return_date=return_date,
                    created_by=admin_user
                )
                transactions.append(transaction)

                # Update book status
                if not is_returned:
                    book.status = 'ISSUED'
                    book.available_copies -= 1
                else:
                    book.available_copies = min(book.total_copies, book.available_copies + 1)
                    if book.available_copies == book.total_copies:
                        book.status = 'AVAILABLE'
                book.save()

        self.stdout.write(f'Created {len(transactions)} sample transactions')

        # Create reading logs
        reading_logs = []
        for _ in range(50):
            user = random.choice(members)
            book = random.choice(books)

            # Create logs for the past 30 days
            log_date = timezone.now().date() - timedelta(days=random.randint(0, 30))

            log, created = ReadingLog.objects.get_or_create(
                user=user,
                book=book,
                log_date=log_date,
                defaults={
                    'read_today': random.choice([True, False]),
                    'pages_read': random.randint(0, 50),
                    'minutes_read': random.randint(0, 120),
                    'notes': random.choice([
                        'Great chapter today!',
                        'Struggled with this part.',
                        'Really enjoying the story.',
                        'Need to read more tomorrow.',
                        'Finished an exciting scene.',
                        ''
                    ]),
                    'progress': random.randint(0, 100)
                }
            )
            if created:
                reading_logs.append(log)

        self.stdout.write(f'Created {len(reading_logs)} sample reading logs')

        # Create book requests
        requests = []
        for _ in range(8):
            user = random.choice(members)
            request_type = random.choice(['WAITLIST', 'PURCHASE'])

            if request_type == 'WAITLIST':
                # Request for an issued book
                issued_books = Book.objects.filter(status='ISSUED')
                if issued_books.exists():
                    book = random.choice(list(issued_books))
                    request, created = BookRequest.objects.get_or_create(
                        user=user,
                        book=book,
                        request_type=request_type,
                        defaults={
                            'reason': 'I\'ve been waiting to read this book.',
                            'status': random.choice(['PENDING', 'APPROVED', 'REJECTED'])
                        }
                    )
                    if created:
                        requests.append(request)
            else:
                # Purchase request
                titles = [
                    'The Winds of Winter', 'The Silmarillion', 'The Wheel of Time',
                    'The Broken Earth Trilogy', 'The Kingkiller Chronicle'
                ]
                request, created = BookRequest.objects.get_or_create(
                    user=user,
                    title=random.choice(titles),
                    author='Unknown',
                    request_type=request_type,
                    defaults={
                        'reason': 'This book would be a great addition to our library.',
                        'status': random.choice(['PENDING', 'APPROVED', 'REJECTED'])
                    }
                )
                if created:
                    requests.append(request)

        self.stdout.write(f'Created {len(requests)} sample book requests')

        # Create club settings
        settings_data = [
            ('issuance_period', '30', 'Default number of days for book issuance'),
            ('max_renewals', '2', 'Maximum number of times a book can be renewed'),
            ('overdue_fine_per_day', '1.00', 'Fine amount per overdue day'),
            ('max_books_per_user', '3', 'Maximum books a user can borrow simultaneously'),
            ('reminder_days_before_due', '3', 'Days before due date to send reminder'),
            ('club_name', 'Company Book Club', 'Name of the book club'),
            ('club_description', 'A community of book lovers sharing knowledge and stories.', 'Description of the book club'),
            ('contact_email', 'bookclub@company.com', 'Contact email for the book club'),
        ]

        for key, value, description in settings_data:
            ClubSettings.objects.get_or_create(
                setting_key=key,
                defaults={
                    'setting_value': value,
                    'description': description,
                    'updated_by': admin_user
                }
            )

        self.stdout.write('Created club settings')

        self.stdout.write(
            self.style.SUCCESS(
                'Sample data created successfully!\n'
                f'Admin user: admin@bookclub.com / admin123\n'
                f'Member users: {len(members)} created (password: password123)\n'
                f'Books: {len(books)}\n'
                f'Transactions: {len(transactions)}\n'
                f'Reading logs: {len(reading_logs)}\n'
                f'Book requests: {len(requests)}'
            )
        )
