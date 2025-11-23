/**
 * Hotkeys System for Gaduka Gang Forum
 * Provides keyboard shortcuts for common actions
 */

class HotkeyManager {
    constructor() {
        this.hotkeys = {
            // Navigation
            'g h': { action: () => window.location.href = '/', description: 'Go to Home' },
            'g f': { action: () => window.location.href = '/forum/', description: 'Go to Forum' },
            'g p': { action: () => window.location.href = '/profile/', description: 'Go to Profile' },
            'g a': { action: () => window.location.href = '/analytics/', description: 'Go to Analytics (Admin)' },

            // Actions
            'c': { action: () => this.createNewTopic(), description: 'Create new topic' },
            'r': { action: () => this.replyToTopic(), description: 'Reply to topic' },
            '/': { action: () => this.focusSearch(), description: 'Focus search' },
            '?': { action: () => this.showHotkeyHelp(), description: 'Show hotkey help' },

            // Moderation (for moderators/admins)
            'm d': { action: () => this.deletePost(), description: 'Delete post (Mod)' },
            'm p': { action: () => this.pinTopic(), description: 'Pin/Unpin topic (Mod)' },

            // Utility
            'Escape': { action: () => this.closeModals(), description: 'Close modals/dialogs' },
            'Ctrl+k': { action: () => this.quickCommand(), description: 'Quick command palette' },
        };

        this.sequence = [];
        this.sequenceTimer = null;
        this.init();
    }

    init() {
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
        this.createHelpModal();
    }

    handleKeyPress(e) {
        // Ignore if typing in input/textarea
        if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
            // Except for Escape and Ctrl+K
            if (e.key !== 'Escape' && !(e.ctrlKey && e.key === 'k')) {
                return;
            }
        }

        // Handle special keys
        if (e.key === 'Escape') {
            this.hotkeys['Escape'].action();
            return;
        }

        if (e.ctrlKey && e.key === 'k') {
            e.preventDefault();
            this.hotkeys['Ctrl+k'].action();
            return;
        }

        // Handle sequence keys
        if (e.key === '?' && !e.shiftKey) {
            return; // Let it through for help
        }

        // Prevent default for hotkey characters
        const key = e.key.toLowerCase();
        if (this.hotkeys[key] || ['g', 'm'].includes(key)) {
            e.preventDefault();
        }

        // Add to sequence
        this.sequence.push(key);

        // Clear sequence timer
        if (this.sequenceTimer) {
            clearTimeout(this.sequenceTimer);
        }

        // Set new timer (1 second to complete sequence)
        this.sequenceTimer = setTimeout(() => {
            this.sequence = [];
        }, 1000);

        // Check for matches
        const sequenceStr = this.sequence.join(' ');

        // Check single key hotkeys
        if (this.hotkeys[key]) {
            this.hotkeys[key].action();
            this.sequence = [];
            return;
        }

        // Check sequence hotkeys
        if (this.hotkeys[sequenceStr]) {
            this.hotkeys[sequenceStr].action();
            this.sequence = [];
            return;
        }
    }

    // Actions
    createNewTopic() {
        const createBtn = document.querySelector('[data-action="create-topic"]');
        if (createBtn) {
            createBtn.click();
        } else {
            // Navigate to create page if button not found
            const currentSection = window.location.pathname.match(/\/section\/(\d+)/);
            if (currentSection) {
                window.location.href = `/topic/create/${currentSection[1]}/`;
            }
        }
    }

    replyToTopic() {
        const replyArea = document.querySelector('#reply-textarea, textarea[name="content"]');
        if (replyArea) {
            replyArea.focus();
            replyArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    focusSearch() {
        const searchInput = document.querySelector('input[type="search"], input[name="search"], #search-input');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }

    showHotkeyHelp() {
        const modal = document.getElementById('hotkey-help-modal');
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    deletePost() {
        // Check if user has mod permissions
        if (!document.body.dataset.userRole || !['moderator', 'admin_level_1', 'admin_level_2', 'admin_level_3', 'super_admin'].includes(document.body.dataset.userRole)) {
            this.showNotification('You do not have permission to delete posts', 'error');
            return;
        }

        const deleteBtn = document.querySelector('.post:focus .delete-btn, .post:hover .delete-btn');
        if (deleteBtn) {
            deleteBtn.click();
        }
    }

    pinTopic() {
        if (!document.body.dataset.userRole || !['moderator', 'admin_level_1', 'admin_level_2', 'admin_level_3', 'super_admin'].includes(document.body.dataset.userRole)) {
            this.showNotification('You do not have permission to pin topics', 'error');
            return;
        }

        const pinBtn = document.querySelector('[data-action="pin-topic"]');
        if (pinBtn) {
            pinBtn.click();
        }
    }

    closeModals() {
        // Close all modals
        document.querySelectorAll('.modal, [role="dialog"]').forEach(modal => {
            modal.style.display = 'none';
        });

        // Close dropdowns
        document.querySelectorAll('.dropdown.open').forEach(dropdown => {
            dropdown.classList.remove('open');
        });
    }

    quickCommand() {
        // TODO: Implement command palette
        this.showNotification('Command palette coming soon!', 'info');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'error' ? '#ff4444' : '#00ff88'};
            color: #000;
            border-radius: 8px;
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    createHelpModal() {
        const modal = document.createElement('div');
        modal.id = 'hotkey-help-modal';
        modal.style.cssText = `
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 9999;
            align-items: center;
            justify-content: center;
        `;

        const content = document.createElement('div');
        content.style.cssText = `
            background: #1a1a2e;
            padding: 30px;
            border-radius: 12px;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            border: 2px solid #00ff88;
        `;

        let html = '<h2 style="color: #00ff88; margin-top: 0;">⌨️ Keyboard Shortcuts</h2>';
        html += '<div style="display: grid; grid-template-columns: 1fr 2fr; gap: 15px; color: #fff;">';

        Object.entries(this.hotkeys).forEach(([key, config]) => {
            html += `
                <div style="font-family: monospace; background: #16213e; padding: 8px; border-radius: 4px; text-align: center;">
                    ${key}
                </div>
                <div style="padding: 8px;">
                    ${config.description}
                </div>
            `;
        });

        html += '</div>';
        html += '<p style="margin-top: 20px; color: #888; font-size: 14px;">Press <kbd>?</kbd> to toggle this help, <kbd>Esc</kbd> to close</p>';

        content.innerHTML = html;
        modal.appendChild(content);
        document.body.appendChild(modal);

        // Close on click outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    }
}

// Initialize hotkeys when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.hotkeyManager = new HotkeyManager();
    });
} else {
    window.hotkeyManager = new HotkeyManager();
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    kbd {
        background: #16213e;
        border: 1px solid #00ff88;
        border-radius: 4px;
        padding: 2px 6px;
        font-family: monospace;
        color: #00ff88;
    }
`;
document.head.appendChild(style);
