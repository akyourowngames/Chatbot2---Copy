/**
 * KAI Extension - Workflow Engine
 * ================================
 * Sequential and conditional action execution
 */

class WorkflowEngine {
    constructor() {
        this.workflows = [];
        this.currentWorkflow = null;
        this.isPaused = false;
    }

    /**
     * Parse workflow from natural language
     * Example: "fill email, click next, wait 2s, fill password, submit"
     */
    parseWorkflow(command) {
        const steps = command.split(',').map(s => s.trim());
        const actions = [];

        for (const step of steps) {
            const action = this.parseStep(step);
            if (action) actions.push(action);
        }

        return {
            id: Date.now().toString(),
            name: `Workflow ${Date.now()}`,
            actions,
            created: new Date().toISOString()
        };
    }

    parseStep(step) {
        const lower = step.toLowerCase();

        // Wait action
        if (lower.startsWith('wait')) {
            const match = step.match(/wait\s+(\d+)\s*(s|ms|second|millisecond)?/i);
            if (match) {
                const duration = parseInt(match[1]);
                const unit = match[2] && match[2].startsWith('m') ? 1 : 1000;
                return { type: 'wait', duration: duration * unit };
            }
        }

        // Fill action  
        if (lower.startsWith('fill') || lower.startsWith('enter')) {
            const match = step.match(/(?:fill|enter)\s+(.+?)(?:\s+with\s+(.+))?$/i);
            if (match) {
                return {
                    type: 'fill',
                    field: match[1],
                    value: match[2] || '{prompt}'  // Prompt user if no value
                };
            }
        }

        // Click action
        if (lower.startsWith('click') || lower.startsWith('press')) {
            const match = step.match(/(?:click|press)\s+(.+)/i);
            if (match) {
                return { type: 'click', target: match[1] };
            }
        }

        // Scroll action
        if (lower.includes('scroll')) {
            return {
                type: 'scroll',
                direction: lower.includes('top') ? 'top' :
                    lower.includes('bottom') ? 'bottom' :
                        lower.includes('up') ? 'up' : 'down'
            };
        }

        // Navigate action
        if (lower.startsWith('go to') || lower.startsWith('navigate')) {
            const match = step.match(/(?:go to|navigate)\s+(.+)/i);
            if (match) {
                return { type: 'navigate', url: match[1] };
            }
        }

        // Generic action
        return { type: 'command', command: step };
    }

    /**
     * Execute workflow
     */
    async executeWorkflow(workflow, context = {}) {
        this.currentWorkflow = workflow;
        this.isPaused = false;
        const results = [];

        console.log(`[Workflow] Executing: ${workflow.name}`);

        for (let i = 0; i < workflow.actions.length; i++) {
            if (this.isPaused) {
                console.log('[Workflow] Paused');
                break;
            }

            const action = workflow.actions[i];
            console.log(`[Workflow] Step ${i + 1}/${workflow.actions.length}:`, action.type);

            try {
                const result = await this.executeAction(action, context);
                results.push({ action, result, success: true });
            } catch (error) {
                console.error(`[Workflow] Error at step ${i + 1}:`, error);
                results.push({ action, error: error.message, success: false });

                // Stop on error unless specified otherwise
                if (!workflow.continueOnError) {
                    break;
                }
            }
        }

        this.currentWorkflow = null;
        return {
            workflow: workflow.name,
            completed: results.length,
            total: workflow.actions.length,
            results
        };
    }

    /**
     * Execute single action
     */
    async executeAction(action, context) {
        switch (action.type) {
            case 'wait':
                await this.wait(action.duration);
                return { waited: action.duration };

            case 'fill':
                return await this.fillField(action.field, action.value, context);

            case 'click':
                return await this.clickElement(action.target);

            case 'scroll':
                return this.scroll(action.direction);

            case 'navigate':
                return await this.navigate(action.url);

            case 'command':
                // Execute as normal KAI command
                return await this.executeCommand(action.command);

            default:
                throw new Error(`Unknown action type: ${action.type}`);
        }
    }

    // Action implementations

    wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async fillField(fieldHint, value, context) {
        // Use existing KAI field filling logic
        if (typeof handleFillField === 'function') {
            return handleFillField(fieldHint, value);
        }
        throw new Error('Field filling not available');
    }

    async clickElement(target) {
        const buttons = document.querySelectorAll('button, input[type="submit"], a.btn, [role="button"]');
        const lower = target.toLowerCase();

        for (const btn of buttons) {
            const text = (btn.textContent || btn.value || '').toLowerCase();
            if (text.includes(lower) || lower.includes(text)) {
                btn.click();
                return { clicked: btn.textContent || btn.value || 'button' };
            }
        }

        throw new Error(`Button "${target}" not found`);
    }

    scroll(direction) {
        const scrollOptions = { behavior: 'smooth' };

        switch (direction) {
            case 'top':
                window.scrollTo({ top: 0, ...scrollOptions });
                break;
            case 'bottom':
                window.scrollTo({ top: document.body.scrollHeight, ...scrollOptions });
                break;
            case 'up':
                window.scrollBy({ top: -500, ...scrollOptions });
                break;
            case 'down':
                window.scrollBy({ top: 500, ...scrollOptions });
                break;
        }

        return { scrolled: direction };
    }

    async navigate(url) {
        // Add https:// if not present
        if (!url.startsWith('http')) {
            url = 'https://' + url;
        }

        window.location.href = url;
        return { navigated: url };
    }

    async executeCommand(command) {
        // Execute through normal KAI command system
        if (typeof handleChatCommand === 'function') {
            return await handleChatCommand(command);
        }
        throw new Error('Command execution not available');
    }

    /**
     * Save workflow for later use
     */
    saveWorkflow(workflow) {
        const existing = this.workflows.findIndex(w => w.id === workflow.id);
        if (existing >= 0) {
            this.workflows[existing] = workflow;
        } else {
            this.workflows.push(workflow);
        }
        this.persistWorkflows();
        return workflow.id;
    }

    /**
     * Load workflows from storage
     */
    async loadWorkflows() {
        try {
            const data = await chrome.storage.local.get(['kai_workflows']);
            this.workflows = data.kai_workflows || [];
            return this.workflows;
        } catch (e) {
            console.error('[Workflow] Load error:', e);
            return [];
        }
    }

    /**
     * Persist workflows to storage
     */
    async persistWorkflows() {
        try {
            await chrome.storage.local.set({ kai_workflows: this.workflows });
        } catch (e) {
            console.error(' [Workflow] Save error:', e);
        }
    }

    /**
     * Get workflow by name or ID
     */
    getWorkflow(nameOrId) {
        return this.workflows.find(w =>
            w.id === nameOrId || w.name.toLowerCase() === nameOrId.toLowerCase()
        );
    }

    /**
     * Pause current workflow
     */
    pause() {
        this.isPaused = true;
    }

    /**
     * Resume paused workflow
     */
    resume() {
        this.isPaused = false;
    }
}

// Global instance
window.kaiWorkflow = new WorkflowEngine();
