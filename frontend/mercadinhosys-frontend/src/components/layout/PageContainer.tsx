import React, { ReactNode } from 'react';

interface PageContainerProps {
    children: ReactNode;
    /** Classes extras para casos específicos (raro — o padrão já cobre a maioria). */
    className?: string;
}

/**
 * Container padrão de página. Fonte única de verdade para o "chassi" de qualquer
 * tela do sistema, garantindo comportamento sólido em mobile e desktop:
 *
 * - `w-full max-w-full min-w-0`: nunca ultrapassa a largura do conteúdo pai, e
 *   `min-w-0` permite que filhos com `truncate`/flex encolham em vez de estourar.
 * - `space-y-6`: ritmo vertical consistente entre seções.
 * - O padding lateral é responsabilidade do `<main>` do MainLayout (p-4/p-6),
 *   então NÃO duplicamos aqui — evita padding dobrado.
 *
 * Use sempre com [PageHeader] no topo. Ver [layout-modais-zindex].
 */
export const PageContainer: React.FC<PageContainerProps> = ({ children, className = '' }) => {
    return (
        <div className={`w-full max-w-full min-w-0 space-y-6 ${className}`}>
            {children}
        </div>
    );
};

export default PageContainer;
