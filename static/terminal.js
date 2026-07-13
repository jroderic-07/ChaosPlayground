class LabTerminal {
    constructor(containerEl, labId) {
        this.containerEl = containerEl;
        this.labId = labId;
        this.term = null;
        this.fitAddon = null;
        this.ws = null;
        this.resizeObserver = null;

        this._initTerminal();
        this._connect();
        this._bindResize();
        this._bindClipboard();
    }

    _initTerminal() {
        this.term = new Terminal({
            cursorBlink: true,
            fontSize: 13,
            fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
            theme: {
                background: '#0a0a0a',
                foreground: '#e5e7eb',
                cursor: '#22d3ee',
                selectionBackground: '#1a3a4a',
            },
            scrollback: 1000,
            allowProposedApi: true,
        });

        const FitAddonCtor = window.FitAddon?.FitAddon || window.FitAddon;
        this.fitAddon = new FitAddonCtor();
        this.term.loadAddon(this.fitAddon);
        this.term.open(this.containerEl);
        this.fitAddon.fit();
        this.term.focus();
    }

    _connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${window.location.host}/ws/labs/${this.labId}`;

        this.ws = new WebSocket(url);

        this.ws.onmessage = (event) => {
            this.term.write(event.data);
        };

        this.ws.onclose = (event) => {
            if (!this._disposed) {
                const detail = event.code === 4404
                    ? 'sandbox not active — start the lab first'
                    : event.code === 1011
                      ? 'server failed to attach shell session'
                      : `code ${event.code}`;
                console.warn(`[terminal] WebSocket closed lab_id=${this.labId} reason=${detail}`);
                this.term.writeln(`\r\n\x1b[33m[disconnected: ${detail}]\x1b[0m`);
            }
        };

        this.ws.onerror = () => {
            console.error(`[terminal] WebSocket error lab_id=${this.labId} url=${url}`);
            this.term.writeln('\r\n\x1b[31m[connection error — check server logs]\x1b[0m');
        };

        this.term.onData((data) => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(data);
            }
        });
    }

    _bindClipboard() {
        this._onPaste = async (event) => {
            if (!this.term || this._disposed) {
                return;
            }
            event.preventDefault();
            const text = event.clipboardData?.getData('text') ?? await this._readClipboard();
            if (text) {
                this._paste(text);
            }
        };

        this._onCopyClick = () => this._copy();
        this._onPasteClick = async () => {
            const text = await this._readClipboard();
            if (text) {
                this._paste(text);
            }
        };

        this.containerEl.addEventListener('paste', this._onPaste);

        this.term.attachCustomKeyEventHandler((event) => {
            if (event.type !== 'keydown') {
                return true;
            }

            if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'v') {
                event.preventDefault();
                this._readClipboard().then((text) => {
                    if (text) {
                        this._paste(text);
                    }
                });
                return false;
            }

            if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'c') {
                if (this.term.hasSelection()) {
                    event.preventDefault();
                    this._copy();
                    return false;
                }
            }

            return true;
        });

        const copyBtn = document.getElementById('terminal-copy-btn');
        const pasteBtn = document.getElementById('terminal-paste-btn');
        if (copyBtn) {
            copyBtn.addEventListener('click', this._onCopyClick);
            this._copyBtn = copyBtn;
        }
        if (pasteBtn) {
            pasteBtn.addEventListener('click', this._onPasteClick);
            this._pasteBtn = pasteBtn;
        }
    }

    async _readClipboard() {
        try {
            return await navigator.clipboard.readText();
        } catch (err) {
            console.warn('[terminal] Clipboard read failed — use Ctrl+Shift+V', err);
            return '';
        }
    }

    _paste(text) {
        if (!this.term || this._disposed) {
            return;
        }
        this.term.focus();
        this.term.paste(text);
    }

    _copy() {
        if (!this.term || !this.term.hasSelection()) {
            return;
        }
        const text = this.term.getSelection();
        navigator.clipboard.writeText(text).catch((err) => {
            console.warn('[terminal] Clipboard write failed — use Ctrl+Shift+C', err);
        });
    }

    _bindResize() {
        this._onResize = () => {
            if (this.fitAddon && this.term) {
                this.fitAddon.fit();
            }
        };

        window.addEventListener('resize', this._onResize);

        if (typeof ResizeObserver !== 'undefined') {
            this.resizeObserver = new ResizeObserver(this._onResize);
            this.resizeObserver.observe(this.containerEl);
        }
    }

    dispose() {
        this._disposed = true;

        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
            this.resizeObserver = null;
        }

        if (this._onResize) {
            window.removeEventListener('resize', this._onResize);
        }

        if (this._onPaste) {
            this.containerEl.removeEventListener('paste', this._onPaste);
        }

        if (this._copyBtn && this._onCopyClick) {
            this._copyBtn.removeEventListener('click', this._onCopyClick);
        }
        if (this._pasteBtn && this._onPasteClick) {
            this._pasteBtn.removeEventListener('click', this._onPasteClick);
        }

        if (this.ws) {
            if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
                this.ws.close(1000, 'Client navigated away');
            }
            this.ws = null;
        }

        if (this.term) {
            this.term.dispose();
            this.term = null;
        }

        this.fitAddon = null;
    }
}

function disposeLabTerminal() {
    if (window.labTerminal) {
        window.labTerminal.dispose();
        window.labTerminal = null;
    }
}

function initLabTerminal() {
    const terminalEl = document.getElementById('terminal');
    if (!terminalEl || !terminalEl.dataset.labId) {
        return;
    }

    disposeLabTerminal();
    window.labTerminal = new LabTerminal(terminalEl, terminalEl.dataset.labId);
}

document.addEventListener('DOMContentLoaded', initLabTerminal);
document.body.addEventListener('htmx:afterSwap', initLabTerminal);
document.body.addEventListener('htmx:oobAfterSwap', initLabTerminal);

document.body.addEventListener('htmx:beforeRequest', (event) => {
    disposeLabTerminal();
});

document.body.addEventListener('htmx:beforeSwap', (event) => {
    const target = event.detail.target;
    if (!target) {
        return;
    }

    if (
        target.id === 'main-content' ||
        target.id === 'terminal-slot' ||
        target.id === 'lab-controls' ||
        target.querySelector?.('#terminal')
    ) {
        disposeLabTerminal();
    }
});

window.addEventListener('beforeunload', disposeLabTerminal);
