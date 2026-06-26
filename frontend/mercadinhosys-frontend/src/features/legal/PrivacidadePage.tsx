import React from 'react';
import LegalLayout, { SecaoTitulo } from './LegalLayout';
import { legalInfo } from './legalInfo';

/**
 * Política de Privacidade (LGPD - Lei 13.709/2018).
 * Conteúdo-base profissional. Revise com apoio jurídico antes do lançamento comercial.
 */
const PrivacidadePage: React.FC = () => {
    return (
        <LegalLayout
            titulo="Política de Privacidade"
            subtitulo="Como o MercadinhoSys trata dados pessoais, em conformidade com a LGPD (Lei nº 13.709/2018)."
        >
            <p>
                Esta Política explica como coletamos, usamos, armazenamos e protegemos dados pessoais ao
                fornecer o {legalInfo.produto}. Ela vale para o lojista assinante, seus usuários e os titulares
                cujos dados são tratados na plataforma.
            </p>

            <SecaoTitulo numero={1}>Papéis: controlador e operador</SecaoTitulo>
            <p>
                A LGPD distingue quem decide sobre o tratamento (controlador) de quem trata em nome de outro
                (operador):
            </p>
            <ul className="list-disc pl-5 space-y-1">
                <li>
                    <strong>Dados da conta do lojista</strong> (cadastro do assinante e seus usuários): atuamos
                    como <strong>controladores</strong>, pois decidimos sobre esse tratamento para prestar o serviço.
                </li>
                <li>
                    <strong>Dados inseridos pelo lojista</strong> (clientes finais, funcionários, fornecedores): o
                    <strong> lojista é o controlador</strong> e nós atuamos como <strong>operadores</strong>,
                    tratando esses dados apenas conforme as instruções dele e esta Política.
                </li>
            </ul>

            <SecaoTitulo numero={2}>Dados que tratamos</SecaoTitulo>
            <ul className="list-disc pl-5 space-y-1">
                <li><strong>Cadastrais:</strong> nome, e-mail, telefone, CPF/CNPJ, dados do estabelecimento.</li>
                <li><strong>De clientes finais do lojista:</strong> nome, contato, CPF, histórico de compras e fiado.</li>
                <li><strong>De funcionários do lojista:</strong> dados cadastrais, jornada e registros de ponto.</li>
                <li>
                    <strong>Dados sensíveis e biométricos:</strong> quando o lojista utiliza o registro de ponto
                    por foto, pode haver tratamento de imagem facial, considerada dado pessoal sensível. Esse uso
                    é configurado e instruído pelo lojista, a quem cabe obter a base legal adequada perante seus
                    funcionários.
                </li>
                <li><strong>De uso:</strong> registros de acesso, logs de auditoria, endereço IP e dados técnicos para segurança.</li>
            </ul>

            <SecaoTitulo numero={3}>Para que usamos</SecaoTitulo>
            <ul className="list-disc pl-5 space-y-1">
                <li>Operar as funcionalidades contratadas (vendas, estoque, fiscal, financeiro, RH/ponto).</li>
                <li>Autenticar usuários e garantir a segurança e a rastreabilidade (auditoria).</li>
                <li>Emitir e importar documentos fiscais quando solicitado.</li>
                <li>Prestar suporte e comunicar avisos importantes sobre o serviço.</li>
                <li>Cumprir obrigações legais e regulatórias.</li>
            </ul>

            <SecaoTitulo numero={4}>Bases legais</SecaoTitulo>
            <p>
                O tratamento se apoia, conforme o caso, na <strong>execução de contrato</strong> (art. 7º, V),
                no <strong>cumprimento de obrigação legal/regulatória</strong> (art. 7º, II — ex.: fiscal e
                trabalhista), no <strong>legítimo interesse</strong> (art. 7º, IX — ex.: segurança e prevenção a
                fraudes) e no <strong>consentimento</strong> quando exigido, especialmente para dados sensíveis.
            </p>

            <SecaoTitulo numero={5}>Compartilhamento</SecaoTitulo>
            <p>Não vendemos dados pessoais. Podemos compartilhá-los apenas com:</p>
            <ul className="list-disc pl-5 space-y-1">
                <li><strong>Provedores de infraestrutura</strong> (hospedagem e banco de dados em nuvem) que processam dados sob contrato.</li>
                <li><strong>Gateways fiscais</strong> (ex.: para emissão de NFC-e/NF-e), estritamente para emitir os documentos solicitados.</li>
                <li><strong>Autoridades públicas</strong>, quando exigido por lei ou ordem judicial.</li>
            </ul>

            <SecaoTitulo numero={6}>Armazenamento e segurança</SecaoTitulo>
            <p>
                Os dados são armazenados em servidores em nuvem com controles de acesso, criptografia em
                trânsito, backups e registros de auditoria. Adotamos medidas técnicas e organizacionais
                razoáveis para proteger os dados contra acessos não autorizados, perda ou alteração indevida.
                Nenhum sistema é 100% imune; em caso de incidente relevante, seguiremos os procedimentos da LGPD.
            </p>

            <SecaoTitulo numero={7}>Retenção</SecaoTitulo>
            <p>
                Mantemos os dados pelo tempo necessário às finalidades acima e ao cumprimento de obrigações
                legais (por exemplo, prazos fiscais e trabalhistas). Encerrada a conta, os dados podem ser
                eliminados ou anonimizados, ressalvadas as hipóteses de guarda obrigatória previstas em lei.
            </p>

            <SecaoTitulo numero={8}>Direitos do titular</SecaoTitulo>
            <p>Nos termos da LGPD, o titular pode solicitar:</p>
            <ul className="list-disc pl-5 space-y-1">
                <li>confirmação da existência de tratamento e acesso aos dados;</li>
                <li>correção de dados incompletos, inexatos ou desatualizados;</li>
                <li>anonimização, bloqueio ou eliminação de dados desnecessários ou excessivos;</li>
                <li>portabilidade e informação sobre compartilhamentos;</li>
                <li>revogação do consentimento.</li>
            </ul>
            <p>
                Quando atuamos como operadores (dados de clientes/funcionários do lojista), os pedidos devem ser
                direcionados ao lojista (controlador); nós o apoiamos no atendimento.
            </p>

            <SecaoTitulo numero={9}>Cookies</SecaoTitulo>
            <p>
                Utilizamos cookies e tecnologias semelhantes essenciais para autenticação e funcionamento do
                sistema (por exemplo, manter a sessão iniciada). Você pode gerenciar cookies no navegador, mas
                desativá-los pode afetar o uso da plataforma.
            </p>

            <SecaoTitulo numero={10}>Encarregado (DPO) e contato</SecaoTitulo>
            <p>
                Para exercer direitos ou esclarecer dúvidas sobre privacidade, fale com nosso encarregado pelo
                tratamento de dados:{' '}
                <a href={`mailto:${legalInfo.emailPrivacidade}`} className="text-blue-600 font-semibold underline">
                    {legalInfo.emailPrivacidade}
                </a>.
            </p>

            <SecaoTitulo numero={11}>Alterações</SecaoTitulo>
            <p>
                Esta Política pode ser atualizada. Mudanças relevantes serão comunicadas pelos canais da
                plataforma, com indicação da nova data de atualização.
            </p>

            <p className="text-xs text-slate-400 pt-4 border-t border-slate-100">
                Vigente desde {legalInfo.vigenciaDesde}. Em conformidade com a Lei nº 13.709/2018 (LGPD).
            </p>
        </LegalLayout>
    );
};

export default PrivacidadePage;
