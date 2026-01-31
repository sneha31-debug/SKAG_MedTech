from typing import Callable, Dict, List, Any
import asyncio
from collections import defaultdict


class EventBus:
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._history: List[Dict[str, Any]] = []
        self._max_history = 1000

    def subscribe(self, event_type: str, callback: Callable) -> None:
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)

    async def publish(self, event_type: str, payload: Any) -> None:
        event_record = {
            "event_type": event_type,
            "payload": payload,
        }
        self._history.append(event_record)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        callbacks = self._subscribers.get(event_type, [])
        wildcard_callbacks = self._subscribers.get("*", [])
        
        all_callbacks = callbacks + wildcard_callbacks
        
        for callback in all_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, payload)
                else:
                    callback(event_type, payload)
            except Exception:
                pass

    def get_history(self, event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        if event_type:
            filtered = [e for e in self._history if e["event_type"] == event_type]
        else:
            filtered = self._history
        return filtered[-limit:]

    def clear_history(self) -> None:
        self._history = []


event_bus = EventBus()
