import { useEffect, useRef, useState, type RefObject } from 'react';

interface Options {
    threshold?: number;   // distância (px) para disparar o refresh
    maxPull?: number;     // limite visual do arraste
    enabled?: boolean;
}

/**
 * Pull-to-refresh para PWA instalado (modo standalone), onde o navegador NÃO
 * oferece o "puxar para atualizar" nativo. Atribui handlers de toque ao
 * elemento rolável (ex.: <main>) e dispara onRefresh quando o usuário arrasta
 * para baixo estando no topo do scroll.
 *
 * Retorna a distância atual do arraste e o estado de refresh para o indicador.
 */
export function usePullToRefresh(
    scrollRef: RefObject<HTMLElement | null>,
    onRefresh: () => void | Promise<void>,
    { threshold = 70, maxPull = 120, enabled = true }: Options = {},
) {
    const [distance, setDistance] = useState(0);
    const [refreshing, setRefreshing] = useState(false);
    const startY = useRef<number | null>(null);
    const pulling = useRef(false);

    useEffect(() => {
        const el = scrollRef.current;
        if (!el || !enabled) return;

        const onTouchStart = (e: TouchEvent) => {
            // Só inicia se já está no topo do conteúdo rolável.
            if (el.scrollTop <= 0 && e.touches.length === 1) {
                startY.current = e.touches[0].clientY;
                pulling.current = true;
            } else {
                pulling.current = false;
                startY.current = null;
            }
        };

        const onTouchMove = (e: TouchEvent) => {
            if (!pulling.current || startY.current === null || refreshing) return;
            const delta = e.touches[0].clientY - startY.current;
            if (delta > 0 && el.scrollTop <= 0) {
                // Resistência: o arraste "pesa" mais perto do limite.
                const d = Math.min(maxPull, delta * 0.5);
                setDistance(d);
                if (e.cancelable) e.preventDefault(); // evita o bounce e segura o gesto
            } else if (delta <= 0) {
                setDistance(0);
            }
        };

        const onTouchEnd = async () => {
            if (!pulling.current) return;
            pulling.current = false;
            const atingiu = distance >= threshold;
            if (atingiu) {
                setRefreshing(true);
                setDistance(threshold);
                try {
                    await onRefresh();
                } finally {
                    // onRefresh normalmente recarrega a página; o reset é defensivo.
                    setRefreshing(false);
                    setDistance(0);
                }
            } else {
                setDistance(0);
            }
            startY.current = null;
        };

        el.addEventListener('touchstart', onTouchStart, { passive: true });
        el.addEventListener('touchmove', onTouchMove, { passive: false });
        el.addEventListener('touchend', onTouchEnd, { passive: true });
        el.addEventListener('touchcancel', onTouchEnd, { passive: true });

        return () => {
            el.removeEventListener('touchstart', onTouchStart);
            el.removeEventListener('touchmove', onTouchMove);
            el.removeEventListener('touchend', onTouchEnd);
            el.removeEventListener('touchcancel', onTouchEnd);
        };
    }, [scrollRef, onRefresh, threshold, maxPull, enabled, distance, refreshing]);

    return { distance, refreshing, threshold };
}

export default usePullToRefresh;
