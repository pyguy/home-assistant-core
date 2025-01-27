"""Platform for Roth Touchline floor heating controller."""
from __future__ import annotations

from typing import NamedTuple

from pytouchline import PyTouchline
import voluptuous as vol

from homeassistant.components.climate import (
    PLATFORM_SCHEMA,
    ClimateEntity,
    ClimateEntityFeature,
)
from homeassistant.components.climate.const import HVAC_MODE_HEAT
from homeassistant.const import ATTR_TEMPERATURE, CONF_HOST, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType


class PresetMode(NamedTuple):
    """Settings for preset mode."""

    mode: int
    program: int


PRESET_MODES = {
    "Normal": PresetMode(mode=0, program=0),
    "Night": PresetMode(mode=1, program=0),
    "Holiday": PresetMode(mode=2, program=0),
    "Pro 1": PresetMode(mode=0, program=1),
    "Pro 2": PresetMode(mode=0, program=2),
    "Pro 3": PresetMode(mode=0, program=3),
}

TOUCHLINE_HA_PRESETS = {
    (settings.mode, settings.program): preset
    for preset, settings in PRESET_MODES.items()
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required(CONF_HOST): cv.string})


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Touchline devices."""

    host = config[CONF_HOST]
    py_touchline = PyTouchline()
    number_of_devices = int(py_touchline.get_number_of_devices(host))
    devices = []
    for device_id in range(0, number_of_devices):
        devices.append(Touchline(PyTouchline(device_id)))
    add_entities(devices, True)


class Touchline(ClimateEntity):
    """Representation of a Touchline device."""

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )

    def __init__(self, touchline_thermostat):
        """Initialize the Touchline device."""
        self.unit = touchline_thermostat
        self._name = None
        self._current_temperature = None
        self._target_temperature = None
        self._current_operation_mode = None
        self._preset_mode = None

    def update(self):
        """Update thermostat attributes."""
        self.unit.update()
        self._name = self.unit.get_name()
        self._current_temperature = self.unit.get_current_temperature()
        self._target_temperature = self.unit.get_target_temperature()
        self._preset_mode = TOUCHLINE_HA_PRESETS.get(
            (self.unit.get_operation_mode(), self.unit.get_week_program())
        )

    @property
    def hvac_mode(self):
        """Return current HVAC mode.

        Need to be one of HVAC_MODE_*.
        """
        return HVAC_MODE_HEAT

    @property
    def hvac_modes(self):
        """Return list of possible operation modes."""
        return [HVAC_MODE_HEAT]

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def preset_mode(self):
        """Return the current preset mode."""
        return self._preset_mode

    @property
    def preset_modes(self):
        """Return available preset modes."""
        return list(PRESET_MODES)

    def set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        preset_mode = PRESET_MODES[preset_mode]
        self.unit.set_operation_mode(preset_mode.mode)
        self.unit.set_week_program(preset_mode.program)

    def set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        self._current_operation_mode = HVAC_MODE_HEAT

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._target_temperature = kwargs.get(ATTR_TEMPERATURE)
        self.unit.set_target_temperature(self._target_temperature)
