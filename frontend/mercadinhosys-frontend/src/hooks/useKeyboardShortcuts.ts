import { useEffect, useRef } from 'react';

/**
 * Hook genérico de atalhos de teclado.
 *
 * Cada atalho é descrito por um "combo" normalizado (modificadores em ordem
 * ctrl→alt→shift→meta + a tecla em minúsculo), ex.: 'f1', 'f9', 'escape',
 * 'ctrl+k', 'shift+?'. Por padrão os atalhos NÃO disparam enquanto o usuário
 * digita em um campo (input/textarea/select/contenteditable) — passe
 * `allowInInput: true` para teclas que devem funcionar mesmo digitando
 * (típico de teclas de função no PDV).
 */
export interface ShortcutHandler {
    combo: string;
    handler: (e: KeyboardEvent) => void;
    /** Dispara mesmo com foco em um campo de digitação. Padrão: false. */
    allowInInput?: boolean;
    /** Chama preventDefault no evento. Padrão: true. */
    preventDefault?: boolean;
}

/** Monta o combo normalizado a partir do evento. */
export function eventToCombo(e: KeyboardEvent): string {
    const parts: string[] = [];
    if (e.ctrlKey) parts.push('ctrl');
    if (e.altKey) parts.push('alt');
    if (e.shiftKey) parts.push('shift');
    if (e.metaKey) parts.push('meta');
    const k = e.key.length === 1 ? e.key.toLowerCase() : e.key.toLowerCase();
    parts.push(k === ' ' ? 'space' : k);
    return parts.join('+');
}

/** Indica se o alvo do evento é um campo editável. */
export function isEditableTarget(target: EventTarget | null): boolean {
    const el = target as HTMLElement | null;
    if (!el || !el.tagName) return false;
    const tag = el.tagName.toUpperCase();
    return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || el.isContentEditable === true;
}

export function useKeyboardShortcuts(shortcuts: ShortcutHandler[], enabled = true): void {
    // Mantém a lista atual sem reanexar o listener a cada render.
    const ref = useRef(shortcuts);
    ref.current = shortcuts;

    useEffect(() => {
        if (!enabled) return;
        const onKeyDown = (e: KeyboardEvent) => {
            const combo = eventToCombo(e);
            for (const s of ref.current) {
                if (s.combo !== combo) continue;
                if (!s.allowInInput && isEditableTarget(e.target)) continue;
                if (s.preventDefault !== false) e.preventDefault();
                s.handler(e);
                break;
            }
        };
        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, [enabled]);
}

export default useKeyboardShortcuts;
