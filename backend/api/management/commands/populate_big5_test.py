import json
from django.core.management.base import BaseCommand
from api.models import PersonalityQuestion
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Load personality questions from a JSON file'

    def handle(self, *args, **kwargs):
        file_path = 'api/data/personality_questions.json'

        try:
            with open(file_path, 'r') as file:
                data = json.load(file)

            created_count = 0
            skipped_count = 0
            
            for item in data:
                text = item.get('text')
                reverse_scale = item.get('keyed') == 'minus'
                facet = item.get('facet')
                domain = item.get('domain')
                
                try:
                    # Try to create the new question
                    PersonalityQuestion.objects.create(
                        text=text,
                        reverse_scale=reverse_scale,
                        facet=facet,
                        domain=domain,
                    )
                    created_count += 1
                except IntegrityError:
                    # This will catch duplicate text entries (since text is unique)
                    self.stdout.write(self.style.WARNING(f'Skipping duplicate question: {text[:50]}'))
                    skipped_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating question "{text[:50]}": {str(e)}'))
                    skipped_count += 1

            self.stdout.write(self.style.SUCCESS(f'Import complete: {created_count} questions created, {skipped_count} skipped'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('Error decoding the JSON file'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {e}'))
            