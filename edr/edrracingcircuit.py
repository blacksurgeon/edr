from edtime import EDTime
from edentities import EDPlanetaryLocation
from edri18n import _, _c

class EDRRacingCircuit(object):
    def __init__(self, properties, player):
        self.waypoints = properties.get("waypoints", [])
        self.type = properties.get("type", None)
        self.category = properties.get("category", None)
        self.laps = properties.get("laps", None)
        self.radius = properties.get("wp_radius", 0.100)
        self.max_altitude = properties.get("max_altitude", 1000)
        self._current_wp = 0
        self.start_time = None
        self.lap_times = []
        self.best = {"lap": None, "race": None}
        self.planet_radius = properties.get("planet_radius", 6371)
        self.player = player
    
    def restart(self):
        self.start_time = None
        self._current_wp = 0
        self.lap_times = []
    
    def reset(self):
        self.restart()
        self.best = {"lap": None, "race": None}

    def update(self):
        # TODO check piloted_vehicle type if it matches
        if self._is_finished():
            return False
        if self.wp_cleared(self.player.piloted_vehicle.attitude):
            return self.advance()
        return True

    def current_waypoint(self):
        if self._is_finished():
            return None
        waypoint = self.waypoints[self._current_wp]
        if "radius" not in waypoint:
           waypoint["radius"] = self.radius
        if "max_altitude" not in waypoint:
           waypoint["max_altitude"] = self.max_altitude
        return self.waypoints[self._current_wp]

    def wp_cleared(self, position):
        wp = self.current_waypoint()
        if not wp:
            return False
        ploc = EDPlanetaryLocation(wp)
        distance = ploc.distance(position, self.planet_radius)
        return distance <= wp["radius"] and position["altitude"] <= wp["max_altitude"]

    def disqualified(self, attitude):
        wp = self.current_waypoint()
        if not wp:
            return altitude > self.max_altitude
        return altitude > wp["max_altitude"]

    def in_progress(self):
        return self.start_time and not self._is_finished()

    def advance(self):
        now = EDTime.py_epoch_now()
        if not self.waypoints:
            return False

        if len(self.waypoints) == 1:
            return False
        
        if self._current_wp is None:
            return False

        if self._current_wp == 0 and len(self.lap_times) == 0:
            print("Race started")
            self.start_time = now

        self._current_wp = (self._current_wp + 1)
        if self._current_wp >= len(self.waypoints):
            if len(self.lap_times) <= self.laps:
                print("Lap finished")
                previous_laps_total = sum(self.lap_times) if self.lap_times else 0
                lap_time = now - self.start_time - previous_laps_total
                self.lap_times.append(lap_time)
                self.best["lap"] = min(lap_time, self.best["lap"] or now)
            if self._is_finished():
                print("Race finished")
                self._current_wp = None
                self.best["race"] = min(now - self.start_time, self.best["race"] or now)
                print(self.lap_times)
                print(self.best)
                return False
            self._current_wp = 0
        return True

    def summarize(self):
        details = []
        if not self.current_waypoint():
            return details

        if not self._is_in_progress():
            details.append(_(u"Proceed to first waypoint to start the race"))
        else:
            details.append(_(u"Go go go!"))

        destination = EDPlanetaryLocation(self.current_waypoint())
        current = self.player.piloted_vehicle.attitude
        bearing = destination.bearing(current)
        distance = destination.distance(current, self.planet_radius)
        pitch = destination.pitch(current, distance) if distance and distance >= 1.0 else "---"
        details.append(_(u">>> {} <<< [{}]  ({}km)").format(bearing, distance, pitch))
        details.append(_(u"Best: {} | lap: {}").format(self.best["race"], self.best["lap"]))
        for lap in self.lap_times:
            details.append(_(u"Lap {}: {}").format(lap, self.lap_times[lap]))
        return details

    def _is_finished(self):
        if self.type == "loop":
            return len(self.lap_times) >= self.laps
        return self._curent_wp is None or self._current_wp >= len(self.waypoints)