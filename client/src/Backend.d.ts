// Type declarations for Backend.js

// ---- Response types ----

export interface ModelStats {
  accuracy: number;
  model_type: string;
  classification_report: Record<string, unknown>;
}

export interface DeviceModel {
  trained_model_stats: ModelStats | null;
}

export interface Device {
  id: string;
  name: string;
  entity_id: string | null;
  beacon_id: string | null;
  model: DeviceModel | null;
  /** Computed by GetDevices */
  trained: boolean;
  /** Computed by GetDevices */
  accuracy: number | string;
  /** Computed by GetDevices */
  identifier: string;
  /** Computed by GetDevices */
  type: "Monitor" | "Beacon" | "Both" | "-";
  /** Populated by location polling */
  location?: string;
}

export interface DeviceLocation {
  device_id: string;
  room: string;
  confidence: number;
}

export interface Tracker {
  id: string;
  entity_id: string;
  mobile: boolean;
  whitelist: boolean;
  blacklist: boolean;
}

export interface Sensor {
  id: string;
  entity_id: string;
  mobile: boolean;
}

export interface Room {
  id: string;
  name: string;
  color: string;
}

export interface BeaconMonitor {
  id: string;
  entity_id: string;
}

export interface TrainingProgress {
  status: string;
  room: string;
  samples: number;
}

export interface HAEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
}

// ---- Input types ----

export interface DeviceInput {
  id?: string;
  name: string;
  entity_id?: string | null;
  beacon_id?: string | null;
}

export interface TrackerInput {
  id?: string;
  entity_id: string;
  mobile?: boolean;
  whitelist?: boolean;
  blacklist?: boolean;
}

export interface SensorInput {
  id?: string;
  entity_id: string;
  mobile: boolean;
}

export interface RoomInput {
  id?: string;
  name: string;
  color: string;
}

// ---- Backend class ----

export class Backend {
  // Devices
  static GetDevices(): Promise<Device[]>;
  static CheckEntityId(entityId: string): Promise<boolean>;
  static CreateDevice(device: DeviceInput): Promise<Device>;
  static UpdateDevice(device: DeviceInput & { id: string }): Promise<Device>;
  static RemoveDevice(device: { id: string }): Promise<unknown>;
  static GetDeviceLocations(): Promise<DeviceLocation[]>;
  static GetDeviceLocation(device_id: string): Promise<DeviceLocation | null>;

  // Trackers (legacy)
  static GetTrackers(): Promise<Tracker[]>;
  static CreateTracker(tracker: TrackerInput): Promise<Tracker>;
  static UpdateTracker(tracker: TrackerInput & { id: string }): Promise<Tracker>;
  static RemoveTracker(tracker: { id: string }): Promise<unknown>;

  // Sensors
  static GetSensors(): Promise<Sensor[]>;
  static CreateSensor(sensor: SensorInput): Promise<Sensor>;
  static UpdateSensor(sensor: SensorInput): Promise<Sensor>;
  static RemoveSensor(sensor: { id: string }): Promise<unknown>;

  // Rooms
  static GetRooms(): Promise<Room[]>;
  static CreateRoom(room: RoomInput): Promise<Room>;
  static UpdateRoom(room: RoomInput & { id: string }): Promise<Room>;
  static RemoveRoom(room: { id: string }): Promise<unknown>;

  // Beacon Monitors
  static GetBeaconMonitors(): Promise<BeaconMonitor[]>;
  static CreateBeaconMonitor(entityId: string): Promise<BeaconMonitor>;
  static RemoveBeaconMonitor(entityId: string): Promise<unknown>;

  // Training
  static GetTrainingProgress(device_id: string): Promise<TrainingProgress | null>;
  static StartTraining(device_id: string, room_id: string, overwrite: boolean): Promise<unknown>;
  static StopTraining(device_id: string): Promise<unknown>;
  static CancelTraining(device_id: string): Promise<unknown>;
  static ChangeRoom(device_id: string, room_id: string): Promise<unknown>;

  // Home Assistant Entities
  static GetHAEntities(domain?: string): Promise<HAEntity[] | null>;
}
