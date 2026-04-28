import logging
import os
import re
import threading
import time
from dataclasses import dataclass

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

from . import config

logger = logging.getLogger(__name__)


def append_to_dataframe(dataframe, data, include_new_columns=False):
    data_df = pd.DataFrame(data, index=[0])
    if not include_new_columns:
        # drop columns not in dataframe from data_df
        # data_df = data_df[data_df.columns.difference(dataframe.columns)]
        data_df.drop(columns=[col for col in data_df if col not in dataframe.columns], inplace=True)

    logger.debug("Appending data row:\n%s", data_df.head())
    dataframe = pd.concat([dataframe, data_df], ignore_index=True)
    return dataframe


class Model(object):
    def __init__(
        self,
        data_path,
        data=None,
        trained_model=None,
        trained_model_stats=None,
        scaler=None,
        data_gatherer=None,
        trained_columns=None,
    ):
        if data is None:
            self.data = pd.DataFrame()
        else:
            self.data = data

        self.trained_model = trained_model
        self.trained_model_stats = trained_model_stats
        self.data_path = data_path
        self.scaler = scaler
        self.current_room = None
        self.data_gatherer = data_gatherer
        self.trained_columns = trained_columns

    @staticmethod
    def get_model_filepath(data_path):
        return os.path.join(data_path, "model.pkl")

    @staticmethod
    def get_data_filepath(data_path):
        return os.path.join(data_path, "data.csv")

    @staticmethod
    def get_scaler_filepath(data_path):
        return os.path.join(data_path, "scaler.pkl")

    def __repr__(self):
        return ("Model(data_path = {}, trained_model_stats = {})").format(self.data_path, self.trained_model_stats)

    def start_recording(self):
        self.stop_recording_flag = False
        if self.current_room is not None:
            self.recording_thread = threading.Thread(target=self.recording_loop)
            self.recording_thread.start()
        else:
            raise Exception("No room selected")

    def stop_recording(self):
        self.stop_recording_flag = True
        self.recording_thread.join()
        logger.debug("Recording stopped. Data shape: %s", self.data.shape)
        self.recording_thread = None
        self.trained_model, self.trained_model_stats = self.train()

    def train(self):
        if self.data.empty or "room" not in self.data.columns:
            logger.warning("Training aborted: no data collected")
            return None, None

        n_rooms = self.data["room"].nunique()
        if n_rooms < 2:
            logger.warning(
                "Training aborted: need at least 2 rooms, got %d. Data is preserved for next session.",
                n_rooms,
            )
            return None, None

        X, Y = self.data_prep(self.data.copy(deep=True))

        if X.empty or Y.empty:
            logger.warning("Training aborted: no usable feature columns after data prep")
            return None, None

        self.trained_columns = list(Y.columns)

        # Need enough samples per class for a train/test split
        min_samples = Y.sum().min()  # one-hot encoded, so sum = count per room
        if min_samples < 2:
            logger.warning(
                "Training aborted: need at least 2 samples per room, smallest room has %d",
                int(min_samples),
            )
            return None, None

        X = self.apply_scaler(X, fit=True)
        X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2, random_state=42)
        classifiers = [RandomForestClassifier(n_estimators=100, random_state=42)]
        best_acc = 0
        best_model_type = ""
        best_model_stats = None
        best_model = None
        for c in classifiers:
            c.fit(X_train, y_train)
            y_pred = c.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            report = classification_report(y_test, y_pred, output_dict=True)
            if acc > best_acc:
                best_acc = acc
                best_model_type = c.__class__.__name__
                best_model_stats = report
                best_model = c
        return best_model, Model_Stats(best_model_type, best_model_stats, best_acc)

    def retrain(self):
        self.trained_model, self.trained_model_stats = self.train()

    def apply_scaler(self, data, fit=False, output_dataframe=True):
        # keep data columns to add them back to scaler output
        data_columns = data.columns
        if fit:
            self.scaler = MinMaxScaler()
            self.scaler.fit(data)
        data = self.scaler.transform(data)
        if output_dataframe:
            data = pd.DataFrame(data, columns=data_columns)
        return data

    @staticmethod
    def _coerce_numeric(df, exclude_cols=None):
        """Convert all columns to numeric where possible, drop non-convertible ones."""
        exclude_cols = set(exclude_cols or [])
        for col in df.columns:
            if col in exclude_cols:
                continue
            df[col] = pd.to_numeric(df[col], errors="coerce")
        # Drop columns that are entirely NaN after coercion (were non-numeric)
        feature_cols = [c for c in df.columns if c not in exclude_cols]
        all_nan = [c for c in feature_cols if df[c].isna().all()]
        if all_nan:
            logger.warning("Dropping non-numeric columns: %s", all_nan)
            df.drop(columns=all_nan, inplace=True)
        return df

    def data_prep_prediction(self, df):
        # df needs to have same columns as self.data
        # if df has more columns, drop them
        # if df has less columns, fill them with max value
        df.drop(columns=[col for col in df if col not in self.data.columns], inplace=True)
        df = df.reindex(columns=self.data.columns, fill_value=0)
        # drop columns [room, Unnamed: 0]
        if "room" in df.columns:
            df.drop(["room"], axis=1, inplace=True)
        df = self._coerce_numeric(df)
        numeric_max = df.max()
        df.fillna(numeric_max, inplace=True)
        return df

    def data_prep(self, df):
        df = self._coerce_numeric(df, exclude_cols=["room"])
        numeric_max = df.drop(columns=["room"], errors="ignore").max()
        df.fillna(numeric_max, inplace=True)
        g = df.groupby("room")
        df_resampled = g.apply(lambda x: x.sample(g.size().min()).reset_index(drop=True))
        # pandas 3.x moves the groupby key into a MultiIndex; reset to get "room" back as a column
        if "room" not in df_resampled.columns and "room" in df_resampled.index.names:
            df_resampled = df_resampled.reset_index(level="room")
        room_encoded = pd.get_dummies(df_resampled["room"], prefix="room")
        df_encoded = pd.concat([df_resampled, room_encoded], axis=1)
        df_encoded.drop(["room"], axis=1, inplace=True)
        if "Unnamed: 0" in df.columns:
            df.drop(["Unnamed: 0"], axis=1, inplace=True)
        Y = df_encoded.filter(regex=("^room_.*"))
        X = df_encoded.drop(df_encoded.filter(regex="^room_.*").columns, axis=1)
        return X, Y

    def fit_scaler(self, X):
        self.scaler = MinMaxScaler()
        X_norm = self.scaler.fit_transform(X)
        return X_norm

    def get_info(self):
        raise NotImplementedError()

    def recording_loop(self):
        # TODO: implement room flag in the dataframe
        while not self.stop_recording_flag:
            try:
                data_row = self.data_gatherer()
                data_row["room"] = self.current_room
                self.data = append_to_dataframe(self.data, data_row, include_new_columns=True)
                time.sleep(1 / config.SAMPLE_RATE)
            except Exception as e:
                logger.warning("Exception in recording loop: %s", e)

    def set_room(self, room):
        self.current_room = room

    def get_training_progress(self):
        # Get number of samples per room in the self.data dataframe
        if not self.data.empty and "room" in self.data.columns:
            result = self.data.groupby("room").size().reset_index(name="counts")
            result["percentage"] = result["counts"] / config.MINIMUM_TRAINING_SAMPLES
            # max percentage is 1
            result["percentage"] = result["percentage"].apply(lambda x: min(x, 1))
            logger.debug("Training progress:\n%s", result)
            result = result.to_dict(orient="records")
            result_dict = {}
            for r in result:
                result_dict[r["room"]] = {"percentage": r["percentage"], "count": r["counts"]}
            return result_dict
        else:
            return {}

    def predict(self):
        if self.trained_model is not None:
            try:
                data = self.data_gatherer()
                raw_data = pd.DataFrame(data, index=[0])
                data = self.data_prep_prediction(raw_data)
                data = self.apply_scaler(data)
                prediction = self.trained_model.predict_proba(data)
                prediction_dict = {}
                best_prediction = 0
                best_prediction_room = ""
                for c, index in zip(self.trained_columns, range(len(self.trained_columns))):
                    p = prediction[index][0][1]  # probability of being in room c
                    prediction_dict[c] = p
                    if p > best_prediction:
                        best_prediction = p
                        best_prediction_room = c
                # Use removeprefix instead of lstrip to correctly strip "room_" prefix
                prediction_dict["room"] = best_prediction_room.removeprefix("room_")
                prediction_dict["confidence"] = best_prediction
                return prediction_dict
            except Exception as e:
                logger.error("Prediction failed: %s", e, exc_info=True)
                return None
        else:
            return None


@dataclass(repr=True)
class Model_Stats(object):
    model_type: str
    classification_report: dict
    accuracy: float

    def __lt__(self, other):
        return self.accuracy < other.accuracy

    def __gt__(self, other):
        return self.accuracy > other.accuracy

    def __eq__(self, other):
        return self.accuracy == other.accuracy

    def __ne__(self, other):
        return self.accuracy != other.accuracy

    def __le__(self, other):
        return self.accuracy <= other.accuracy

    def __ge__(self, other):
        return self.accuracy >= other.accuracy


class Device(object):
    def __init__(self, name, entity_id=None, beacon_id=None, model=None, data_gatherer=None):
        if entity_id is None and beacon_id is None:
            raise ValueError("At least one of entity_id or beacon_id must be specified")
        self.entity_id = entity_id
        self.beacon_id = beacon_id

        self.name = name
        self.model = model
        self.new_model = None
        self.training = False
        self.data_gatherer = data_gatherer

    def __repr__(self):
        identifier = self.entity_id if self.entity_id is not None else self.beacon_id
        return "Device(name={}, id={}, model={})".format(self.name, identifier, self.model)

    def start_training(self, room, append=False):
        self.training = True
        id = self.entity_id if self.entity_id is not None else self.beacon_id
        if self.model is None:
            self.model = Model(id, data_gatherer=self.data_gatherer)
        if append:
            self.new_model = self.model
            self.new_model.data_gatherer = self.data_gatherer
        else:
            self.new_model = Model(id, data_gatherer=self.data_gatherer)
        self.new_model.set_room(room)
        self.new_model.start_recording()

    def stop_training(self):
        self.training = False
        self.new_model.stop_recording()
        self.model = self.new_model

    def cancel_training(self):
        self.training = False
        self.new_model.stop_recording()
        self.new_model = None

    def retrain(self):
        self.model.retrain()

    def get_location(self):
        if self.model is not None:
            return self.model.predict()
        else:
            return None


class Sensor(object):
    def __init__(self, entity_id, data_source=None, mobile=False):
        self.entity_id = entity_id
        self.mobile = mobile
        self.data_source = data_source

    def __repr__(self):
        return ("Sensor(entity_id={}, mobile={}, data_source={})").format(self.entity_id, self.mobile, self.data_source)

    def get_data(self):
        if self.data_source is not None:
            state = self.data_source.get_entity_state(self.entity_id)
            return self.parse_state(state)
        else:
            raise AttributeError("No data source specified")

    def parse_state(self, state):
        raise NotImplementedError


class Binary_Sensor(Sensor):
    def parse_state(self, state):
        return state.state == "on"


class Smartphone_Tracker(Sensor):
    def __init__(self, entity_id, data_source=None, mobile=False, whitelist=False, blacklist=False):
        super().__init__(entity_id, data_source, mobile)
        self.whitelist = whitelist
        self.blacklist = blacklist

    def parse_state(self, state):
        # drop keys from state.attributes that match the regex sensor\..*\-icon
        attr = {k: v for k, v in state.attributes.items() if not re.match("icon", k)}
        attr = {k: v for k, v in attr.items() if not re.match("friendly_name", k)}
        return attr


# Metadata attribute keys to exclude from beacon monitor data
_BEACON_MONITOR_META_KEYS = frozenset(
    {"options", "device_class", "icon", "friendly_name", "unit_of_measurement", "state_class"}
)


class BeaconMonitor(Sensor):
    """A sensor entity that reports BLE beacon distances/RSSI as attributes.

    Each attribute is keyed by beacon ID (uuid_major_minor) with a numeric value.
    Metadata attributes are filtered out, and only numeric values are kept.
    """

    def parse_state(self, state):
        result = {}
        for key, value in state.attributes.items():
            if key in _BEACON_MONITOR_META_KEYS:
                continue
            # Only keep numeric values (RSSI or distance)
            if isinstance(value, (int, float)):
                result[key] = value
        return result


@dataclass(repr=True)
class Room(object):
    def __init__(self, id, name, color="#ffffffff"):
        self.id = id
        self.name = name
        self.color = color
