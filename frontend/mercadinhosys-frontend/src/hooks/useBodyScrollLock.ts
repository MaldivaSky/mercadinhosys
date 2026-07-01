import { useEffect } from 'react';

let lockCount = 0;
let savedScrollY = 0;
let previousBodyStyle: Partial<CSSStyleDeclaration> = {};

/**
 * Trava o scroll do body enquanto um modal/drawer estiver aberto em mobile.
 *
 * Usa a técnica de `position: fixed` no body (não apenas `overflow: hidden`):
 * apenas overflow:hidden não impede o bounce/rubber-band do Safari iOS, que
 * desloca a página por baixo de overlays "fixed", empurrando botões (ex.:
 * "Fechar") para fora da área tocável — dava a impressão de que o modal
 * "não fecha". Suporta múltiplos modais empilhados via contagem de referências.
 */
function lockBodyScroll() {
    if (lockCount === 0) {
        savedScrollY = window.scrollY;
        previousBodyStyle = {
            position: document.body.style.position,
            top: document.body.style.top,
            left: document.body.style.left,
            right: document.body.style.right,
            width: document.body.style.width,
            overflow: document.body.style.overflow,
        };
        document.body.style.position = 'fixed';
        document.body.style.top = `-${savedScrollY}px`;
        document.body.style.left = '0';
        document.body.style.right = '0';
        document.body.style.width = '100%';
        document.body.style.overflow = 'hidden';
    }
    lockCount += 1;
}

function unlockBodyScroll() {
    lockCount = Math.max(0, lockCount - 1);
    if (lockCount === 0) {
        document.body.style.position = previousBodyStyle.position || '';
        document.body.style.top = previousBodyStyle.top || '';
        document.body.style.left = previousBodyStyle.left || '';
        document.body.style.right = previousBodyStyle.right || '';
        document.body.style.width = previousBodyStyle.width || '';
        document.body.style.overflow = previousBodyStyle.overflow || '';
        window.scrollTo(0, savedScrollY);
    }
}

export function useBodyScrollLock(active: boolean) {
    useEffect(() => {
        if (!active) return;
        lockBodyScroll();
        return () => unlockBodyScroll();
    }, [active]);
}

/**
 * Trava global e automática: observa o DOM inteiro e mantém o body travado
 * enquanto existir qualquer overlay "fixed inset-0" montado (o padrão usado
 * por todos os modais do sistema, inclusive os que não passam por
 * useBodyScrollLock individualmente). Uma única montagem no topo do app cobre
 * todos os modais "crus" do sistema, existentes e futuros, sem precisar
 * instrumentar cada componente manualmente.
 */
export function useGlobalOverlayScrollLock() {
    useEffect(() => {
        let overlayPresente = false;

        const verificar = () => {
            const existe = document.querySelectorAll('.fixed.inset-0').length > 0;
            if (existe === overlayPresente) return;
            overlayPresente = existe;
            if (existe) lockBodyScroll();
            else unlockBodyScroll();
        };

        verificar();
        const observer = new MutationObserver(verificar);
        observer.observe(document.body, { childList: true, subtree: true });

        return () => {
            observer.disconnect();
            if (overlayPresente) unlockBodyScroll();
        };
    }, []);
}
