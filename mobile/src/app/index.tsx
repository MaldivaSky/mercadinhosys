import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Linking, ActivityIndicator, ScrollView, Platform } from 'react-native';
import { GeofenceService } from '../services/GeofenceService';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { useLocalSearchParams } from 'expo-router';

export default function DeliveryScreen() {
  const params = useLocalSearchParams();
  const [customerPhone] = useState('5511999999999');
  const [customerName] = useState('João');
  const [distance, setDistance] = useState<number | null>(null);
  const [gpsPoints, setGpsPoints] = useState<any[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);

  // Instância simulada do destino
  const geofence = new GeofenceService(-23.550520, -46.633308);

  // Verificação na Inicialização (Persistence Local e Token via Deep Link)
  useEffect(() => {
    const init = async () => {
      try {
        // Intercepta token do Deep Link (QR Code) e salva seguro
        if (params.token) {
          await AsyncStorage.setItem('access_token', params.token as string);
        }

        const saved = await AsyncStorage.getItem('rota_atual');
        if (saved) {
          setGpsPoints(JSON.parse(saved));
        }
      } catch (e) {
        console.error("Erro ao iniciar", e);
      }
    };
    init();
  }, [params.token]);

  const savePoint = async (point: any) => {
    try {
      const newPoints = [...gpsPoints, point];
      setGpsPoints(newPoints);
      await AsyncStorage.setItem('rota_atual', JSON.stringify(newPoints));
    } catch (e) {
      console.error("Erro ao salvar KM", e);
    }
  };

  // Envio Real-time para atualizar o Painel Gerencial
  const emitirEventoRealTime = async (status: string, lat: number, lon: number) => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) {
        console.warn('Sem token de autenticação');
        return;
      }

      await fetch('http://localhost:5000/api/logistica/eventos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          venda_id: 1, // Simulando que o entregador está com a Venda #1
          status: status,
          latitude: lat,
          longitude: lon
        })
      });
    } catch (e) {
      console.error("Erro ao emitir evento realtime", e);
    }
  };

  const handleSimulateApproaching = () => {
    const lat = -23.554000;
    const lon = -46.633308;
    const currentDist = geofence.checkProximity(lat, lon);
    setDistance(currentDist);
    
    savePoint({ lat, lon, timestamp: new Date().toISOString() });
    
    // Dispara evento de Rastreio contínuo (Em Rota)
    emitirEventoRealTime('EM_ROTA', lat, lon);
  };

  const handleOpenWhatsApp = (type: 'APPROACHING' | 'ARRIVED') => {
    let message = '';
    if (type === 'APPROACHING') {
      message = `Olá ${customerName}! Sou o entregador do MercadinhoSys. Já estou virando a esquina e chego em 2 minutinhos com as suas compras! 🏍️`;
    } else {
      message = `Olá ${customerName}! Cheguei aqui na frente com o seu pedido. Estou aguardando você para fazer a entrega! 📦`;
      // Dispara evento de "Chegou no Local" para validade jurídica no ERP
      emitirEventoRealTime('CHEGOU_NO_LOCAL', -23.550520, -46.633308);
    }

    const uri = `https://wa.me/${customerPhone}?text=${encodeURIComponent(message)}`;
    Linking.openURL(uri).catch(() => {
      if (Platform.OS === 'web') {
        window.alert('Navegador bloqueou o pop-up ou WhatsApp Web não está configurado.');
      }
    });
  };

  const syncWithServer = async () => {
    if (gpsPoints.length === 0) {
      if (Platform.OS === 'web') window.alert('Nenhum ponto de GPS para sincronizar.');
      return;
    }

    setIsSyncing(true);
    try {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) {
        if (Platform.OS === 'web') window.alert('Erro: Motorista não autenticado. Leia o QR Code novamente.');
        return;
      }

      // Dispara o Batch de GPS para cálculo de KM e custo (Assíncrono na Fila)
      const res = await fetch('http://localhost:5000/api/logistica/auditoria-batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ pontos_gps: gpsPoints })
      });
      
      // Limpeza apenas se Status 202 (Accepted)
      if (res.status === 202 || res.status === 200) {
        await AsyncStorage.removeItem('rota_atual');
        setGpsPoints([]);
        
        if (Platform.OS === 'web') {
          window.alert('Sucesso! KMs sincronizados com o ERP MercadinhoSys.');
        }
      } else {
        throw new Error('Falha no Servidor');
      }
    } catch (e) {
      if (Platform.OS === 'web') {
        window.alert('Erro de conexão. Os KMs continuam seguros no armazenamento local.');
      }
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <LinearGradient colors={['#141E30', '#243B55']} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        
        <View style={styles.header}>
          <MaterialCommunityIcons name="motorbike" size={48} color="#00ffcc" />
          <Text style={styles.title}>MercadinhoSys</Text>
          <Text style={styles.subtitle}>Painel do Entregador</Text>
        </View>

        <View style={styles.card}>
          <View style={styles.customerInfo}>
            <Ionicons name="person-circle-outline" size={32} color="#fff" />
            <Text style={styles.customerName}>Cliente: {customerName}</Text>
          </View>

          {distance !== null ? (
            <View style={styles.distanceBadge}>
              <Ionicons name="location-sharp" size={24} color="#ff4757" />
              <Text style={styles.distanceText}>
                A {Math.round(distance)} metros
              </Text>
            </View>
          ) : (
            <Text style={styles.waitingText}>Aguardando sinal do GPS...</Text>
          )}

          <TouchableOpacity style={styles.actionBtn} onPress={handleSimulateApproaching}>
            <Ionicons name="navigate" size={20} color="#fff" />
            <Text style={styles.actionBtnText}>Capturar GPS (&lt; 500m)</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.actionsGrid}>
          <TouchableOpacity 
            style={[styles.glassBtn, { borderColor: '#f1c40f' }]} 
            onPress={() => handleOpenWhatsApp('APPROACHING')}
          >
            <Ionicons name="logo-whatsapp" size={24} color="#f1c40f" />
            <Text style={styles.glassBtnText}>Avisar: Chegando</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.glassBtn, { borderColor: '#2ecc71' }]} 
            onPress={() => handleOpenWhatsApp('ARRIVED')}
          >
            <Ionicons name="checkmark-circle" size={24} color="#2ecc71" />
            <Text style={styles.glassBtnText}>Estou no Local</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.storageCard}>
          <View style={styles.storageHeader}>
            <Ionicons name="cloud-offline" size={20} color="#bdc3c7" />
            <Text style={styles.storageTitle}>Armazenamento Offline</Text>
          </View>
          <Text style={styles.storageDesc}>
            {gpsPoints.length} pontos de GPS salvos de forma resiliente.
          </Text>

          <TouchableOpacity 
            style={[styles.syncBtn, gpsPoints.length === 0 && styles.syncBtnDisabled]} 
            onPress={syncWithServer}
            disabled={isSyncing || gpsPoints.length === 0}
          >
            {isSyncing ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Ionicons name="cloud-upload" size={20} color="#fff" />
                <Text style={styles.syncBtnText}>Finalizar Turno (Sync)</Text>
              </>
            )}
          </TouchableOpacity>
        </View>
        
      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scrollContent: { padding: 20, paddingTop: 60, paddingBottom: 40 },
  header: { alignItems: 'center', marginBottom: 30 },
  title: { fontSize: 28, fontWeight: 'bold', color: '#00ffcc', marginTop: 10, letterSpacing: 1 },
  subtitle: { fontSize: 16, color: '#bdc3c7', marginTop: 5, textTransform: 'uppercase', letterSpacing: 2 },
  card: { backgroundColor: 'rgba(255, 255, 255, 0.1)', borderRadius: 20, padding: 20, marginBottom: 20, borderWidth: 1, borderColor: 'rgba(255, 255, 255, 0.2)' },
  customerInfo: { flexDirection: 'row', alignItems: 'center', marginBottom: 20 },
  customerName: { fontSize: 18, color: '#fff', marginLeft: 10, fontWeight: '600' },
  distanceBadge: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255, 71, 87, 0.2)', paddingVertical: 12, borderRadius: 12, marginBottom: 20, borderWidth: 1, borderColor: 'rgba(255, 71, 87, 0.5)' },
  distanceText: { fontSize: 22, color: '#ff4757', fontWeight: 'bold', marginLeft: 8 },
  waitingText: { color: '#bdc3c7', textAlign: 'center', marginBottom: 20, fontStyle: 'italic' },
  actionBtn: { backgroundColor: '#3498db', flexDirection: 'row', justifyContent: 'center', alignItems: 'center', paddingVertical: 15, borderRadius: 12, elevation: 3 },
  actionBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold', marginLeft: 10 },
  actionsGrid: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 30 },
  glassBtn: { flex: 0.48, backgroundColor: 'rgba(255, 255, 255, 0.05)', borderWidth: 1, borderRadius: 15, paddingVertical: 15, alignItems: 'center', justifyContent: 'center' },
  glassBtnText: { color: '#fff', fontSize: 14, fontWeight: '600', marginTop: 8 },
  storageCard: { backgroundColor: 'rgba(0, 0, 0, 0.3)', borderRadius: 15, padding: 20 },
  storageHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  storageTitle: { color: '#bdc3c7', fontSize: 16, fontWeight: '600', marginLeft: 10 },
  storageDesc: { color: '#fff', fontSize: 14, marginBottom: 20 },
  syncBtn: { backgroundColor: '#9b59b6', flexDirection: 'row', justifyContent: 'center', alignItems: 'center', paddingVertical: 14, borderRadius: 10 },
  syncBtnDisabled: { backgroundColor: 'rgba(155, 89, 182, 0.5)' },
  syncBtnText: { color: '#fff', fontSize: 16, fontWeight: 'bold', marginLeft: 10 }
});
