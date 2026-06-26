import React from 'react';
import LegalLayout, { SecaoTitulo } from './LegalLayout';
import { legalInfo } from './legalInfo';

/**
 * Termos de Uso do MercadinhoSys.
 * Conteúdo-base profissional. Revise com apoio jurídico antes de cobrar/assinar contrato.
 */
const TermosPage: React.FC = () => {
    return (
        <LegalLayout
            titulo="Termos de Uso"
            subtitulo={`Condições para utilização da plataforma ${legalInfo.produto}.`}
        >
            <div className="rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
                Ao criar uma conta ou utilizar o {legalInfo.produto}, você declara que leu, entendeu e
                concorda com estes Termos de Uso e com a nossa{' '}
                <a href="/privacidade" className="font-bold underline">Política de Privacidade</a>.
            </div>

            <SecaoTitulo numero={1}>Quem somos</SecaoTitulo>
            <p>
                O {legalInfo.produto} é um sistema de gestão para comércio varejista (frente de caixa/PDV,
                controle de estoque, clientes, financeiro e emissão de documentos fiscais), oferecido como
                serviço por assinatura (SaaS) por {legalInfo.razaoSocial}, inscrita no CNPJ {legalInfo.cnpj},
                com sede em {legalInfo.cidadeUf} ("nós", "plataforma").
            </p>

            <SecaoTitulo numero={2}>Definições</SecaoTitulo>
            <ul className="list-disc pl-5 space-y-1">
                <li><strong>Cliente/Assinante:</strong> a pessoa física ou jurídica (o lojista) que contrata o serviço.</li>
                <li><strong>Usuário:</strong> cada pessoa autorizada pelo Cliente a acessar o sistema (admin, gerente, caixa etc.).</li>
                <li><strong>Conta:</strong> o cadastro do estabelecimento e seus usuários na plataforma.</li>
                <li><strong>Dados do Cliente:</strong> as informações inseridas pelo Cliente (produtos, vendas, clientes finais, funcionários etc.).</li>
            </ul>

            <SecaoTitulo numero={3}>Cadastro e conta</SecaoTitulo>
            <p>
                Para usar a plataforma é necessário criar uma conta com informações verdadeiras e atualizadas.
                O Cliente é responsável por manter a confidencialidade de suas credenciais e por todas as
                atividades realizadas pelos Usuários de sua conta. Avise-nos imediatamente em caso de uso não
                autorizado.
            </p>

            <SecaoTitulo numero={4}>Planos, pagamento e cancelamento</SecaoTitulo>
            <ul className="list-disc pl-5 space-y-1">
                <li>O serviço é oferecido em planos, cujas funcionalidades e preços são informados no momento da contratação.</li>
                <li>A assinatura é cobrada de forma recorrente (mensal), salvo condição diferente acordada por escrito.</li>
                <li>O Cliente pode cancelar a qualquer momento; o cancelamento encerra as renovações futuras, sem reembolso de períodos já pagos, salvo quando exigido por lei.</li>
                <li>Eventuais períodos de teste gratuito ou cortesia são concedidos a nosso critério e podem ser encerrados a qualquer tempo.</li>
            </ul>

            <SecaoTitulo numero={5}>Uso aceitável</SecaoTitulo>
            <p>O Cliente e os Usuários comprometem-se a não:</p>
            <ul className="list-disc pl-5 space-y-1">
                <li>utilizar a plataforma para fins ilícitos ou que violem direitos de terceiros;</li>
                <li>tentar acessar áreas, dados ou contas de outros estabelecimentos;</li>
                <li>comprometer a segurança, a integridade ou o desempenho do serviço (ataques, engenharia reversa, automações abusivas);</li>
                <li>inserir dados que não tenham autorização legal para tratar.</li>
            </ul>

            <SecaoTitulo numero={6}>Documentos fiscais (NFC-e / NF-e)</SecaoTitulo>
            <p>
                A plataforma oferece recursos para emissão e importação de documentos fiscais eletrônicos. A
                emissão com valor fiscal depende de requisitos sob responsabilidade do Cliente, entre eles:
                CNPJ ativo e regular, certificado digital próprio, credenciamento na SEFAZ e parâmetros
                tributários corretos (NCM, CSOSN/CST, CFOP). <strong>A correção tributária e a conformidade
                fiscal são de responsabilidade do Cliente e de seu contador.</strong> Recursos em ambiente de
                homologação ou simulado não possuem valor fiscal e destinam-se apenas a testes.
            </p>

            <SecaoTitulo numero={7}>Dados do Cliente e propriedade</SecaoTitulo>
            <p>
                Os Dados do Cliente pertencem ao Cliente. Nós os tratamos apenas para operar e melhorar o
                serviço, conforme a <a href="/privacidade" className="text-blue-600 font-semibold underline">Política de Privacidade</a>.
                O Cliente pode exportar seus dados enquanto a conta estiver ativa. Toda a propriedade
                intelectual da plataforma (software, marca, layout) permanece conosco.
            </p>

            <SecaoTitulo numero={8}>Disponibilidade e suporte</SecaoTitulo>
            <p>
                Empregamos esforços para manter o serviço disponível, mas ele é fornecido "no estado em que se
                encontra", podendo haver interrupções para manutenção, atualizações ou por fatores externos
                (provedores de hospedagem, internet, SEFAZ). O suporte é prestado pelos canais informados na
                página de <a href="/ajuda" className="text-blue-600 font-semibold underline">Ajuda</a>.
            </p>

            <SecaoTitulo numero={9}>Limitação de responsabilidade</SecaoTitulo>
            <p>
                Na máxima extensão permitida pela lei, não nos responsabilizamos por lucros cessantes, perda de
                dados decorrente de uso indevido, ou prejuízos indiretos. O Cliente é responsável por manter
                boas práticas de uso e por conferir as informações fiscais e financeiras geradas. Recomendamos
                que o Cliente mantenha seus próprios registros e backups quando aplicável.
            </p>

            <SecaoTitulo numero={10}>Alterações nos Termos</SecaoTitulo>
            <p>
                Podemos atualizar estes Termos para refletir melhorias ou exigências legais. Mudanças
                relevantes serão comunicadas pelos canais da plataforma. O uso continuado após a vigência
                significa concordância com a versão atualizada.
            </p>

            <SecaoTitulo numero={11}>Lei aplicável e foro</SecaoTitulo>
            <p>
                Estes Termos são regidos pelas leis da República Federativa do Brasil. Fica eleito o foro da
                comarca de {legalInfo.cidadeUf} para dirimir controvérsias, salvo disposição legal em contrário.
            </p>

            <SecaoTitulo numero={12}>Contato</SecaoTitulo>
            <p>
                Dúvidas sobre estes Termos:{' '}
                <a href={`mailto:${legalInfo.emailContato}`} className="text-blue-600 font-semibold underline">
                    {legalInfo.emailContato}
                </a>.
            </p>

            <p className="text-xs text-slate-400 pt-4 border-t border-slate-100">
                Documento em vigor desde {legalInfo.vigenciaDesde}.
            </p>
        </LegalLayout>
    );
};

export default TermosPage;
