import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { isEditableTarget } from '../hooks/useKeyboardShortcuts';
import { NAV_CHORDS } from './registry';
import ShortcutsHelp from './ShortcutsHelp';

/**
 * Atalhos globais da aplicação autenticada:
 *  - "?"           → abre/fecha a ajuda de atalhos
 *  - "Esc"         → fecha a ajuda (quando aberta)
 *  - "G" + tecla   → navegação rápida entre telas (estilo GitHub/Linear)
 *
 * Montado uma única vez no MainLayout. Ignora eventos enquanto o usuário digita
 * em campos, para nunca atrapalhar a digitação.
 */
const CHORD_TIMEOUT_MS = 1000;

const GlobalShortcuts: React.FC = () => {
    const navigate = useNavigate();
    const [helpOpen, setHelpOpen] = useState(false);
    const lastGRef = useRef(0);

    useEffect(() => {
        const onKeyDown = (e: KeyboardEvent) => {
            // "?" abre a ajuda mesmo fora de campos; dentro de campo, ignora.
            if (e.key === '?' && !isEditableTarget(e.target)) {
                e.preventDefault();
                setHelpOpen((v) => !v);
                return;
            }
            if (e.key === 'Escape' && helpOpen) {
                setHelpOpen(false);
                return;
            }

            // Navegação por chord "G" + tecla — nunca dentro de campos de texto.
            if (isEditableTarget(e.target)) return;
            const key = e.key.toLowerCase();
            const agora = Date.now();

            if (key === 'g' && !e.ctrlKey && !e.altKey && !e.metaKey) {
                lastGRef.current = agora;
                return;
            }
            if (agora - lastGRef.current < CHORD_TIMEOUT_MS) {
                const destino = NAV_CHORDS[key];
                if (destino) {
                    e.preventDefault();
                    lastGRef.current = 0;
                    navigate(destino);
                }
            }
        };
        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, [navigate, helpOpen]);

    return <ShortcutsHelp open={helpOpen} onClose={() => setHelpOpen(false)} />;
};

export default GlobalShortcuts;
