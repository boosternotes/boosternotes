from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from myapp.db_backup import backup_to_dropbox, restore_from_dropbox, list_backups


@login_required
@require_http_methods(['GET', 'POST'])
def backup_panel(request):
    # Only superusers/staff can access
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Staff only.')
        return redirect('dashboard')

    backups = []
    try:
        backups = list_backups()
    except Exception as e:
        messages.warning(request, f'Could not load backup list: {str(e)}')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'backup':
            try:
                timestamp = backup_to_dropbox()
                messages.success(
                    request,
                    f'✅ Backup successful! Saved as db_{timestamp}.sqlite3 on Dropbox.'
                )
            except Exception as e:
                messages.error(request, f'❌ Backup failed: {str(e)}')

        elif action == 'restore':
            selected_file = request.POST.get('restore_file', '').strip()
            if not selected_file:
                messages.error(request, '❌ Please select a backup file to restore.')
            else:
                try:
                    restore_from_dropbox(selected_file)
                    messages.success(
                        request,
                        f'✅ Database restored from {selected_file} successfully! Restart the server if changes are not visible.'
                    )
                except Exception as e:
                    messages.error(request, f'❌ Restore failed: {str(e)}')

        return redirect('backup_panel')

    return render(request, 'backup_panel.html', {
        'backups': backups,
        'page_title': 'DB Backup & Restore',
    })
