/**
 * SCRIPT DE DIAGNÓSTICO RÁPIDO PARA FOTOS
 * 
 * COMO USAR:
 * 1. Abra o Console do Navegador (F12)
 * 2. Abra a aba "Console" 
 * 3. Cole todo este conteúdo e pressione Enter
 * 4. Observe os logs detalhados sobre o status das fotos
 * 
 * Este script vai:
 * - Chamar a API de histórico
 * - Mostrar exatamente quais campos estão sendo retornados
 * - Indicar se foto_url existe ou não
 * - Mostrar o valor de cada foto encontrada
 */

(async function diagnosticarFotos() {
  console.log('%c🔍 INICIANDO DIAGNÓSTICO DE FOTOS...', 'color: blue; font-size: 14px; font-weight: bold;');
  
  try {
    const today = new Date().toISOString().split('T')[0];
    const url = `/api/ponto/historico?data_inicio=${today}&data_fim=${today}&per_page=100`;
    
    console.log(`%c📍 Chamando: ${url}`, 'color: gray;');
    
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      }
    });

    const data = await response.json();
    
    console.log('%c✅ RESPOSTA COMPLETA DA API:', 'color: green; font-weight: bold;');
    console.table(data);
    
    if (!data.data || data.data.length === 0) {
      console.warn('%c⚠️ NENHUM REGISTRO ENCONTRADO PARA HOJE!', 'color: orange; font-weight: bold;');
      return;
    }

    console.log('%c📊 ANÁLISE DETALHADA:', 'color: blue; font-weight: bold;');
    console.log(`Total de registros: ${data.data.length}`);

    // Analisa cada registro
    data.data.forEach((registro, index) => {
      console.group(`%c📋 Registro ${index + 1}`, 'color: purple; font-weight: bold;');
      console.log('Tipo:', registro.tipo_registro);
      console.log('Data:', registro.data);
      console.log('Hora:', registro.hora);
      console.log('Funcionário:', registro.funcionario_nome);
      console.log('---');
      console.log('Campos encontrados:', Object.keys(registro));
      console.log('---');
      
      if (registro.foto_url) {
        console.log('%c✅ foto_url ENCONTRADO:', 'color: green; font-weight: bold;', registro.foto_url);
      } else {
        console.log('%c❌ foto_url NÃO ENCONTRADO', 'color: red; font-weight: bold;');
      }

      if (registro.foto) {
        console.log('%c⚠️ Campo "foto" encontrado (não "foto_url"):', 'color: orange;', 
          `${String(registro.foto).substring(0, 100)}...`);
      }

      if (registro.foto_base64) {
        console.log('%c⚠️ Campo "foto_base64" encontrado:', 'color: orange;', 
          `${String(registro.foto_base64).substring(0, 100)}...`);
      }

      console.groupEnd();
    });

    // Resumo final
    console.log('%c📈 RESUMO:', 'color: blue; font-weight: bold;');
    const comFoto = data.data.filter(r => r.foto_url).length;
    const semFoto = data.data.length - comFoto;
    console.log(`✅ Com foto_url: ${comFoto}`);
    console.log(`❌ Sem foto_url: ${semFoto}`);
    
    if (semFoto > 0) {
      console.warn('%c⚠️ PROBLEMA DETECTADO: Fotos não estão sendo retornadas!', 'color: orange; font-weight: bold;');
      console.log('Possíveis causas:');
      console.log('1. Backend não está salvando a foto no banco');
      console.log('2. Backend está salvando mas não retornando foto_url no GET');
      console.log('3. Campo tem nome diferente (foto, foto_base64, image_url, etc)');
    } else {
      console.log('%c✅ SUCESSO: Todas as fotos estão sendo retornadas!', 'color: green; font-weight: bold;');
    }

  } catch (error) {
    console.error('%c❌ ERRO NA REQUISIÇÃO:', 'color: red; font-weight: bold;', error);
  }
})();
