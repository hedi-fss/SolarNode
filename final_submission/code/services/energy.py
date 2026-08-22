"""SolarNode Energy Model"""
import random


class EnergyModel:
    def __init__(
            self,
            battery_capacity=2000,
            avg_current=35,
            solar_current=40):
        self.battery_capacity = battery_capacity  # mAh
        self.avg_current = avg_current  # mA
        self.solar_current = solar_current  # mA (effective)
        self.battery_level = battery_capacity

    def simulate_hour(self, has_solar=True, transmission_count=0):
        """Simulate one hour of operation"""
        # Power consumption (transmissions consume more)
        consumption = self.avg_current + (transmission_count * 0.5)

        # Solar harvesting
        if has_solar:
            efficiency = random.uniform(0.1, 0.9)
            harvested = self.solar_current * efficiency
        else:
            harvested = 0

        # Net drain
        net_drain = consumption - harvested

        # Update battery
        self.battery_level -= net_drain
        self.battery_level = max(
            0, min(self.battery_capacity, self.battery_level))

        return self.battery_level

    def is_dead(self):
        return self.battery_level <= 0
