import * as Speech from 'expo-speech';
import { calculateDistanceInMeters } from '../utils/haversine';

export class GeofenceService {
  private alertTriggered = false;

  constructor(private targetLat: number, private targetLon: number) {}

  public checkProximity(currentLat: number, currentLon: number) {
    const distance = calculateDistanceInMeters(
      currentLat,
      currentLon,
      this.targetLat,
      this.targetLon
    );

    // Se estiver a menos de 500 metros e o alerta ainda não tocou
    if (distance <= 500 && !this.alertTriggered) {
      this.triggerAlert();
      this.alertTriggered = true;
    }
    
    return distance;
  }

  private triggerAlert() {
    Speech.speak('Atenção entregador! Você está chegando no cliente. Aperte o botão na tela para avisar o cliente no WhatsApp.', {
      language: 'pt-BR',
      rate: 1.0,
      pitch: 1.0,
    });
  }

  public resetAlert() {
    this.alertTriggered = false;
  }
}
