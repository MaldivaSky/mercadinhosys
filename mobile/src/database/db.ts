import * as SQLite from 'expo-sqlite';

export const initDB = async () => {
  try {
    const db = await SQLite.openDatabaseAsync('tracking.db');
    
    // Tabela para guardar os pontos offline antes do batch
    await db.execAsync(`
      CREATE TABLE IF NOT EXISTS PosicaoGeografica (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        timestamp TEXT NOT NULL,
        synced INTEGER DEFAULT 0
      );
    `);
    
    console.log('Banco de dados offline inicializado com sucesso.');
    return db;
  } catch (error) {
    console.error('Erro ao inicializar SQLite:', error);
    throw error;
  }
};
