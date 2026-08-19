"""
Management command to migrate existing vendor approval data to new vendor_status field.
Run this after migrating the database schema.

Usage:
    python manage.py migrate_vendor_approval
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from app.models import CustomUser


class Command(BaseCommand):
    help = 'Migrate existing vendor approval data to new vendor_status field'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # Get all vendors
        vendors = CustomUser.objects.filter(role='vendor')
        
        if not vendors.exists():
            self.stdout.write(self.style.SUCCESS('No vendors found. Nothing to migrate.'))
            return
        
        approved_vendors = vendors.filter(is_approved=True)
        pending_vendors = vendors.filter(is_approved=False)
        
        self.stdout.write(
            self.style.WARNING(
                f'Found {vendors.count()} vendors total:\n'
                f'  - {approved_vendors.count()} approved\n'
                f'  - {pending_vendors.count()} not yet approved\n'
            )
        )
        
        migrated_count = 0
        
        if not dry_run:
            # Migrate approved vendors
            for vendor in approved_vendors:
                if vendor.vendor_status != 'approved':
                    vendor.vendor_status = 'approved'
                    if not vendor.vendor_approved_at:
                        vendor.vendor_approved_at = timezone.now()
                    vendor.save()
                    migrated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Set {vendor.email} to approved')
                    )
            
            # Migrate pending vendors
            for vendor in pending_vendors:
                if vendor.vendor_status == 'not_vendor' or vendor.vendor_status == 'pending':
                    vendor.vendor_status = 'pending'
                    vendor.save()
                    migrated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'✓ Set {vendor.email} to pending')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccessfully migrated {migrated_count} vendors to new vendor_status field.'
                )
            )
        else:
            # Dry run - show what would be migrated
            for vendor in approved_vendors:
                if vendor.vendor_status != 'approved':
                    self.stdout.write(f'[DRY RUN] Would set {vendor.email} to approved')
                    migrated_count += 1
            
            for vendor in pending_vendors:
                if vendor.vendor_status != 'pending':
                    self.stdout.write(f'[DRY RUN] Would set {vendor.email} to pending')
                    migrated_count += 1
            
            if migrated_count > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n[DRY RUN] Would migrate {migrated_count} vendors.\n'
                        f'Run without --dry-run to apply changes.'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('All vendors already using new vendor_status field.')
                )
