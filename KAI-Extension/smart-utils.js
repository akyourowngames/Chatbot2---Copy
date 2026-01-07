/**
 * KAI Extension - Smart Utilities
 * =================================
 * Fuzzy matching, NLP helpers, and intelligent suggestions
 */

// ==================== FUZZY MATCHING ====================

/**
 * Calculate Levenshtein distance between two strings
 */
function levenshteinDistance(a, b) {
    const matrix = [];

    for (let i = 0; i <= b.length; i++) {
        matrix[i] = [i];
    }

    for (let j = 0; j <= a.length; j++) {
        matrix[0][j] = j;
    }

    for (let i = 1; i <= b.length; i++) {
        for (let j = 1; j <= a.length; j++) {
            if (b.charAt(i - 1) === a.charAt(j - 1)) {
                matrix[i][j] = matrix[i - 1][j - 1];
            } else {
                matrix[i][j] = Math.min(
                    matrix[i - 1][j - 1] + 1,  // substitution
                    matrix[i][j - 1] + 1,       // insertion
                    matrix[i - 1][j] + 1        // deletion
                );
            }
        }
    }

    return matrix[b.length][a.length];
}

/**
 * Find fuzzy matches for a query in a list
 */
function fuzzyMatch(query, candidates, threshold = 3) {
    const matches = [];
    const queryLower = query.toLowerCase();

    for (const candidate of candidates) {
        const candidateLower = (typeof candidate === 'string' ? candidate : candidate.label || '').toLowerCase();
        const distance = levenshteinDistance(queryLower, candidateLower);

        if (distance <= threshold) {
            matches.push({
                item: candidate,
                score: distance,
                similarity: 1 - (distance / Math.max(queryLower.length, candidateLower.length))
            });
        }
    }

    return matches.sort((a, b) => a.score - b.score);
}

/**
 * Find similar commands
 */
function findSimilarCommands(input, commandList) {
    const words = input.toLowerCase().split(' ');
    const firstWord = words[0];

    const matches = fuzzyMatch(firstWord, commandList.map(c => c.name || c));

    return matches.slice(0, 5).map(m => m.item);
}

// ==================== NATURAL LANGUAGE PARSING ====================

/**
 * Extract entities from natural language
 */
function extractEntities(text) {
    const entities = {};

    // Email
    const emailRegex = /\b[\w.-]+@[\w.-]+\.\w+\b/g;
    const emails = text.match(emailRegex);
    if (emails) entities.email = emails[0];

    // Phone (US format, flexible)
    const phoneRegex = /(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/g;
    const phones = text.match(phoneRegex);
    if (phones) entities.phone = phones[0];

    // URL
    const urlRegex = /https?:\/\/[\w.-]+(?:\.[\w.-]+)+[\w\-._~:/?#[\]@!$&'()*+,;=]*/g;
    const urls = text.match(urlRegex);
    if (urls) entities.url = urls[0];

    // Numbers
    const numberRegex = /\b\d+\b/g;
    const numbers = text.match(numberRegex);
    if (numbers) entities.numbers = numbers.map(n => parseInt(n));

    return entities;
}

/**
 * Parse natural command from conversational input
 */
function parseNaturalCommand(sentence) {
    const entities = extractEntities(sentence);
    const lower = sentence.toLowerCase();

    // "my email is X" or "X is my email"
    if (entities.email && (lower.includes('my email') || lower.includes('email is'))) {
        return {
            intent: 'FILL_FIELD',
            field: 'email',
            value: entities.email,
            confidence: 0.9
        };
    }

    // "my phone is X" or "call me at X"
    if (entities.phone && (lower.includes('phone') || lower.includes('call') || lower.includes('number'))) {
        return {
            intent: 'FILL_FIELD',
            field: 'phone',
            value: entities.phone,
            confidence: 0.9
        };
    }

    // "I'm X" or "my name is X" - extract name
    const nameMatch = sentence.match(/(?:my name is|i'm|i am)\s+([a-z\s]+)/i);
    if (nameMatch) {
        return {
            intent: 'FILL_FIELD',
            field: 'name',
            value: nameMatch[1].trim(),
            confidence: 0.8
        };
    }

    // "go to X" or "open X"
    if ((lower.includes('go to') || lower.includes('open')) && entities.url) {
        return {
            intent: 'NAVIGATE',
            url: entities.url,
            confidence: 0.9
        };
    }

    return null;
}

// ==================== SMART FIELD MATCHING ====================

/**
 * Match field using multiple strategies
 */
function smartMatchField(query, fields) {
    query = query.toLowerCase().trim();

    // Strategy 1: Exact match
    for (const field of fields) {
        const label = (field.label || '').toLowerCase();
        if (label === query) {
            return { field, strategy: 'exact', confidence: 1.0 };
        }
    }

    // Strategy 2: Type matching
    const typeMap = {
        'email': ['email', 'e-mail'],
        'tel': ['phone', 'telephone', 'mobile', 'cell'],
        'password': ['password', 'pwd', 'pass'],
        'text': ['name', 'username', 'user']
    };

    for (const field of fields) {
        const type = (field.type || '').toLowerCase();
        for (const [fieldType, keywords] of Object.entries(typeMap)) {
            if (type === fieldType && keywords.some(k => query.includes(k))) {
                return { field, strategy: 'type', confidence: 0.85 };
            }
        }
    }

    // Strategy 3: Contains match
    for (const field of fields) {
        const label = (field.label || '').toLowerCase();
        if (label.includes(query) || query.includes(label)) {
            return { field, strategy: 'contains', confidence: 0.7 };
        }
    }

    // Strategy 4: Fuzzy match
    const fuzzyMatches = fuzzyMatch(query, fields.map(f => ({ label: f.label, field: f })), 2);
    if (fuzzyMatches.length > 0 && fuzzyMatches[0].score <= 2) {
        return {
            field: fuzzyMatches[0].item.field,
            strategy: 'fuzzy',
            confidence: fuzzyMatches[0].similarity
        };
    }

    // Strategy 5: Word overlap
    const queryWords = query.split(' ');
    for (const field of fields) {
        const labelWords = (field.label || '').toLowerCase().split(' ');
        const overlap = queryWords.filter(w => labelWords.some(lw => lw.includes(w) || w.includes(lw)));

        if (overlap.length > 0) {
            const confidence = overlap.length / Math.max(queryWords.length, labelWords.length);
            if (confidence > 0.3) {
                return { field, strategy: 'word-overlap', confidence };
            }
        }
    }

    return null;
}

/**
 * Suggest similar fields when match fails
 */
function suggestSimilarFields(query, fields) {
    const suggestions = [];

    // Get fuzzy matches with higher threshold
    const fuzzyMatches = fuzzyMatch(query, fields.map(f => ({ label: f.label, field: f })), 5);

    for (const match of fuzzyMatches.slice(0, 5)) {
        suggestions.push({
            field: match.item.field,
            label: match.item.field.label,
            similarity: match.similarity,
            reason: `Similar to "${query}"`
        });
    }

    // Add same-type fields
    const queryType = inferFieldType(query);
    if (queryType) {
        for (const field of fields) {
            if (field.type === queryType && !suggestions.find(s => s.field === field)) {
                suggestions.push({
                    field,
                    label: field.label,
                    similarity: 0.5,
                    reason: `Same type (${queryType})`
                });
            }
        }
    }

    return suggestions.slice(0, 5);
}

/**
 * Infer field type from query
 */
function inferFieldType(query) {
    query = query.toLowerCase();

    if (query.includes('email') || query.includes('e-mail')) return 'email';
    if (query.includes('phone') || query.includes('tel') || query.includes('mobile')) return 'tel';
    if (query.includes('password') || query.includes('pwd')) return 'password';
    if (query.includes('search')) return 'search';
    if (query.includes('date')) return 'date';
    if (query.includes('number') || query.includes('age') || query.includes('count')) return 'number';

    return null;
}

// ==================== ACTION HISTORY ====================

/**
 * Track and manage action history for undo/redo
 */
class ActionHistory {
    constructor(maxSize = 50) {
        this.stack = [];
        this.maxSize = maxSize;
    }

    push(action) {
        this.stack.push({
            ...action,
            timestamp: Date.now(),
            id: `action_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        });

        if (this.stack.length > this.maxSize) {
            this.stack.shift();
        }
    }

    getLast(n = 1) {
        if (n === 1) {
            return this.stack[this.stack.length - 1];
        }
        return this.stack.slice(-n);
    }

    pop() {
        return this.stack.pop();
    }

    getByType(type) {
        return this.stack.filter(a => a.type === type);
    }

    clear() {
        this.stack = [];
    }

    size() {
        return this.stack.length;
    }
}

// Global instance
window.kaiActionHistory = new ActionHistory();

// ==================== EXPORTS ====================

window.kaiUtils = {
    levenshteinDistance,
    fuzzyMatch,
    findSimilarCommands,
    extractEntities,
    parseNaturalCommand,
    smartMatchField,
    suggestSimilarFields,
    inferFieldType,
    ActionHistory
};
