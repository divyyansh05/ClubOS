import { useEffect, useState } from "react";
import {
  fetchEvents,
  createEvent,
  deleteEvent,
  fetchUnconfirmedAnomalies,
  confirmAnomaly,
  dismissAnomaly
} from "../../lib/api";
import type { EventSchema, EventCreateSchema, EventCategory, ImpactMagnitude } from "../../types/events";
import type { SocialAnomaly } from "../../types/clubos";

const CATEGORY_OPTIONS: { value: EventCategory | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "player_signing", label: "Transfers" },
  { value: "player_departure", label: "Transfers" },
  { value: "match_result_win", label: "Matches" },
  { value: "match_result_loss", label: "Matches" },
  { value: "trophy_win", label: "Matches" },
  { value: "trophy_loss", label: "Matches" },
  { value: "commercial_event", label: "Commercial" },
  { value: "media_event", label: "Media" },
  { value: "transfer_window", label: "Transfers" },
  { value: "injury_news", label: "Media" },
];

const CATEGORIES_DEDUPE = ["All", "Transfers", "Matches", "Commercial", "Media"];

const getCategoryIcon = (category: EventCategory): string => {
  switch (category) {
    case "player_signing":
    case "player_departure":
      return "\u{1F3BD}";
    case "match_result_win":
    case "trophy_win":
      return "\u{1F3C6}";
    case "match_result_loss":
    case "trophy_loss":
      return "⚠️";
    case "transfer_window":
      return "\u{1F4C5}";
    case "media_event":
      return "\u{1F4F0}";
    case "commercial_event":
      return "\u{1F4B0}";
    case "injury_news":
      return "🏥";
    default:
      return "📌";
  }
};

const getMagnitudeStyles = (magnitude: ImpactMagnitude): string => {
  switch (magnitude) {
    case "high":
      return "bg-critical-50 text-critical-700 dark:bg-critical-900 dark:text-critical-300 border-critical-200 dark:border-critical-700";
    case "medium":
      return "bg-warning-50 text-warning-700 dark:bg-warning-900 dark:text-warning-300 border-warning-200 dark:border-warning-700";
    case "low":
      return "bg-info-50 text-info-700 dark:bg-info-900 dark:text-info-300 border-info-200 dark:border-info-700";
    default:
      return "bg-stone-50 text-stone-700 dark:bg-stone-800 dark:text-stone-300";
  }
};

export default function EventCalendarPage() {
  const [events, setEvents] = useState<EventSchema[]>([]);
  const [filteredEvents, setFilteredEvents] = useState<EventSchema[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFilter, setSelectedFilter] = useState<string>("All");
  const [showAddForm, setShowAddForm] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  // V1.6.5 — Social Anomaly Detection
  const [anomalies, setAnomalies] = useState<SocialAnomaly[]>([]);
  const [anomaliesLoading, setAnomaliesLoading] = useState(true);
  const [selectedAnomaly, setSelectedAnomaly] = useState<SocialAnomaly | null>(null);
  const [showAnomalyConfirmForm, setShowAnomalyConfirmForm] = useState(false);

  const [formData, setFormData] = useState<EventCreateSchema>({
    event_date: "",
    event_name: "",
    event_category: "commercial_event",
    event_description: "",
    expected_impact: "",
    impact_magnitude: "medium",
  });

  useEffect(() => {
    loadEvents();
    loadAnomalies();
  }, []);

  useEffect(() => {
    applyFilter();
  }, [events, selectedFilter]);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const data = await fetchEvents();
      setEvents(data.items);
    } catch (err) {
      console.error(err);
      setError("Failed to load events. Please check the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const applyFilter = () => {
    if (selectedFilter === "All") {
      setFilteredEvents(events);
    } else {
      const categoryMap: Record<string, EventCategory[]> = {
        Transfers: ["player_signing", "player_departure", "transfer_window"],
        Matches: ["match_result_win", "match_result_loss", "trophy_win", "trophy_loss"],
        Commercial: ["commercial_event"],
        Media: ["media_event", "injury_news"],
      };
      const categories = categoryMap[selectedFilter] || [];
      setFilteredEvents(events.filter((e) => categories.includes(e.event_category)));
    }
  };

  const handleAddEvent = async () => {
    try {
      await createEvent(formData);
      setShowAddForm(false);
      setFormData({
        event_date: "",
        event_name: "",
        event_category: "commercial_event",
        event_description: "",
        expected_impact: "",
        impact_magnitude: "medium",
      });
      loadEvents();
    } catch (err) {
      console.error(err);
      alert("Failed to create event");
    }
  };

  const handleDelete = async (eventId: string) => {
    try {
      await deleteEvent(eventId);
      setDeleteConfirm(null);
      loadEvents();
    } catch (err) {
      console.error(err);
      alert("Failed to delete event");
    }
  };

  // V1.6.5 — Social Anomaly handlers
  const loadAnomalies = async () => {
    try {
      setAnomaliesLoading(true);
      const data = await fetchUnconfirmedAnomalies();
      setAnomalies(data.items);
    } catch (err) {
      console.error(err);
      // Non-blocking error — anomalies are supplementary feature
    } finally {
      setAnomaliesLoading(false);
    }
  };

  const handleConfirmAnomaly = (anomaly: SocialAnomaly) => {
    setSelectedAnomaly(anomaly);
    setShowAnomalyConfirmForm(true);
  };

  const submitAnomalyConfirmation = async () => {
    if (!selectedAnomaly) return;

    try {
      const month = selectedAnomaly.month.substring(0, 7); // YYYY-MM

      await confirmAnomaly(month, {
        confirmed_name: formData.event_name,
        confirmed_category: formData.event_category,
        description: formData.event_description,
        impact_magnitude: formData.impact_magnitude,
        affected_assets: formData.expected_impact || "social_media"
      });

      setShowAnomalyConfirmForm(false);
      setSelectedAnomaly(null);
      setFormData({
        event_date: "",
        event_name: "",
        event_category: "commercial_event",
        event_description: "",
        expected_impact: "",
        impact_magnitude: "medium",
      });
      loadEvents();
      loadAnomalies();
    } catch (err) {
      console.error(err);
      alert("Failed to confirm anomaly");
    }
  };

  const handleDismissAnomaly = async (anomaly: SocialAnomaly) => {
    try {
      const month = anomaly.month.substring(0, 7); // YYYY-MM
      await dismissAnomaly(month);
      loadAnomalies();
    } catch (err) {
      console.error(err);
      alert("Failed to dismiss anomaly");
    }
  };

  // When opening anomaly confirm form, pre-fill formData
  useEffect(() => {
    if (selectedAnomaly && showAnomalyConfirmForm) {
      setFormData({
        event_date: selectedAnomaly.month,
        event_name: selectedAnomaly.candidate_event_name,
        event_category: selectedAnomaly.candidate_category as EventCategory,
        event_description: `Auto-detected from social media anomaly. ${selectedAnomaly.metric} showed ${selectedAnomaly.z_score.toFixed(2)}-sigma deviation in ${selectedAnomaly.month.substring(0, 7)}.`,
        expected_impact: "social_media",
        impact_magnitude: selectedAnomaly.confidence_level === "high" ? "high" : "medium" as ImpactMagnitude,
      });
    }
  }, [selectedAnomaly, showAnomalyConfirmForm]);

  const groupByMonth = (eventList: EventSchema[]): Record<string, EventSchema[]> => {
    const grouped: Record<string, EventSchema[]> = {};
    eventList.forEach((event) => {
      const month = event.event_date.substring(0, 7);
      if (!grouped[month]) grouped[month] = [];
      grouped[month].push(event);
    });
    return grouped;
  };

  const groupedEvents = groupByMonth(filteredEvents);
  const sortedMonths = Object.keys(groupedEvents).sort().reverse();

  if (loading) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <div className="text-center text-stone-500">Loading events...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <div className="text-center text-critical-600">{error}</div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-4xl font-headline text-ink dark:text-paper">Event Calendar</h1>
          <button
            onClick={() => setShowAddForm(true)}
            className="px-4 py-2 bg-sport-blue-600 text-white rounded-lg hover:bg-sport-blue-700 transition-colors font-semibold"
          >
            + Add Event
          </button>
        </div>
        <p className="text-stone-600 dark:text-stone-400">
          Track real-world events that impact your digital metrics. Events appear as annotations on metric charts to
          provide context for KPI movements.
        </p>
      </div>

      {/* Social Anomalies Panel (V1.6.5) */}
      {!anomaliesLoading && anomalies.length > 0 && (
        <div className="mb-8 border-2 border-amber-500 dark:border-amber-600 bg-amber-50 dark:bg-amber-950 p-6 rounded-lg">
          <h2 className="text-2xl font-headline text-amber-900 dark:text-amber-100 mb-2">
            SOCIAL ANOMALIES — PENDING CONFIRMATION
          </h2>
          <p className="text-sm text-amber-800 dark:text-amber-200 mb-4">
            These months show unusual social media activity. Confirm if they correspond to a real-world event to add
            context across all ClubOS metrics.
          </p>
          <div className="space-y-4">
            {anomalies.map((anomaly, idx) => {
              const month_label = anomaly.month.substring(0, 7);
              const month_display = new Date(anomaly.month).toLocaleDateString("en-US", {
                month: "short",
                year: "numeric",
              });

              return (
                <div
                  key={idx}
                  className="bg-white dark:bg-stone-900 border border-amber-200 dark:border-amber-800 rounded-lg p-4 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="px-2 py-1 bg-amber-600 text-white font-mono text-xs font-semibold rounded">
                          {month_display.toUpperCase()}
                        </span>
                        <span
                          className={`px-2 py-0.5 text-xs rounded ${
                            anomaly.confidence_level === "high"
                              ? "bg-critical-100 dark:bg-critical-900 text-critical-700 dark:text-critical-300"
                              : anomaly.confidence_level === "medium"
                              ? "bg-warning-100 dark:bg-warning-900 text-warning-700 dark:text-warning-300"
                              : "bg-info-100 dark:bg-info-900 text-info-700 dark:text-info-300"
                          }`}
                        >
                          {anomaly.confidence_level.toUpperCase()} CONFIDENCE
                        </span>
                      </div>
                      <p className="text-sm text-stone-700 dark:text-stone-300 mb-2">
                        <strong>Detected pattern:</strong> {anomaly.metric.replace(/_/g, " ")} was{" "}
                        {Math.abs(anomaly.z_score).toFixed(1)} standard deviations{" "}
                        {anomaly.direction === "spike" ? "above" : "below"} average — {anomaly.direction} detected.
                      </p>
                      <p className="text-sm text-stone-700 dark:text-stone-300">
                        <strong>{getCategoryIcon(anomaly.candidate_category as EventCategory)} Possible:</strong>{" "}
                        {anomaly.likely_cause.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleConfirmAnomaly(anomaly)}
                        className="px-3 py-2 bg-sport-blue-600 text-white rounded-lg hover:bg-sport-blue-700 transition-colors font-semibold text-sm"
                      >
                        Confirm as Event
                      </button>
                      <button
                        onClick={() => handleDismissAnomaly(anomaly)}
                        className="px-3 py-2 bg-stone-200 dark:bg-stone-700 text-stone-700 dark:text-stone-300 rounded-lg hover:bg-stone-300 dark:hover:bg-stone-600 transition-colors font-semibold text-sm"
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 mb-8 flex-wrap">
        {CATEGORIES_DEDUPE.map((category) => (
          <button
            key={category}
            onClick={() => setSelectedFilter(category)}
            className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
              selectedFilter === category
                ? "bg-sport-blue-600 text-white"
                : "bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-300 hover:bg-stone-200 dark:hover:bg-stone-700"
            }`}
          >
            {category}
          </button>
        ))}
      </div>

      {/* Event List */}
      {filteredEvents.length === 0 ? (
        <div className="text-center py-16 text-stone-500">No events registered for this period</div>
      ) : (
        <div className="space-y-8">
          {sortedMonths.map((month) => (
            <div key={month}>
              <h2 className="text-2xl font-headline text-ink dark:text-paper mb-4">{month}</h2>
              <div className="space-y-4">
                {groupedEvents[month]
                  .sort((a, b) => b.event_date.localeCompare(a.event_date))
                  .map((event) => (
                    <div
                      key={event.event_id}
                      className="bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-700 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-4 flex-1">
                          <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-sport-blue-100 dark:bg-sport-blue-900 flex items-center justify-center text-2xl">
                            {getCategoryIcon(event.event_category)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="text-lg font-semibold text-ink dark:text-paper">{event.event_name}</h3>
                              <span
                                className={`px-2 py-0.5 text-xs rounded border ${getMagnitudeStyles(
                                  event.impact_magnitude
                                )}`}
                              >
                                {event.impact_magnitude.toUpperCase()}
                              </span>
                            </div>
                            <p className="text-sm text-stone-600 dark:text-stone-400 mb-2">{event.event_date}</p>
                            <p className="text-sm text-stone-700 dark:text-stone-300 mb-3">{event.event_description}</p>
                            {event.affected_assets.length > 0 && (
                              <div className="flex flex-wrap gap-2">
                                {event.affected_assets.map((asset) => (
                                  <span
                                    key={asset}
                                    className="px-2 py-1 text-xs rounded bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-300"
                                  >
                                    {asset}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                        <button
                          onClick={() => setDeleteConfirm(event.event_id)}
                          className="text-critical-600 hover:text-critical-700 dark:text-critical-400 dark:hover:text-critical-300 text-sm font-semibold"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Event Form Modal (and Anomaly Confirmation) */}
      {(showAddForm || showAnomalyConfirmForm) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-stone-900 rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-headline text-ink dark:text-paper mb-6">
              {showAnomalyConfirmForm ? "Confirm Social Anomaly as Event" : "Add New Event"}
            </h2>
            {showAnomalyConfirmForm && selectedAnomaly && (
              <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded">
                <p className="text-sm text-amber-800 dark:text-amber-200">
                  Auto-detected: {selectedAnomaly.metric.replace(/_/g, " ")} showed{" "}
                  {Math.abs(selectedAnomaly.z_score).toFixed(1)}σ {selectedAnomaly.direction} in{" "}
                  {selectedAnomaly.month.substring(0, 7)}
                </p>
              </div>
            )}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-stone-700 dark:text-stone-300 mb-1">
                  Event Name
                </label>
                <input
                  type="text"
                  value={formData.event_name}
                  onChange={(e) => setFormData({ ...formData, event_name: e.target.value })}
                  className="w-full px-3 py-2 border border-stone-300 dark:border-stone-600 rounded-lg bg-white dark:bg-stone-800 text-ink dark:text-paper"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-stone-700 dark:text-stone-300 mb-1">Event Date</label>
                <input
                  type="date"
                  value={formData.event_date}
                  onChange={(e) => setFormData({ ...formData, event_date: e.target.value })}
                  className="w-full px-3 py-2 border border-stone-300 dark:border-stone-600 rounded-lg bg-white dark:bg-stone-800 text-ink dark:text-paper"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-stone-700 dark:text-stone-300 mb-1">Category</label>
                <select
                  value={formData.event_category}
                  onChange={(e) => setFormData({ ...formData, event_category: e.target.value as EventCategory })}
                  className="w-full px-3 py-2 border border-stone-300 dark:border-stone-600 rounded-lg bg-white dark:bg-stone-800 text-ink dark:text-paper"
                >
                  <option value="player_signing">Player Signing</option>
                  <option value="player_departure">Player Departure</option>
                  <option value="match_result_win">Match Result Win</option>
                  <option value="match_result_loss">Match Result Loss</option>
                  <option value="trophy_win">Trophy Win</option>
                  <option value="trophy_loss">Trophy Loss</option>
                  <option value="transfer_window">Transfer Window</option>
                  <option value="media_event">Media Event</option>
                  <option value="injury_news">Injury News</option>
                  <option value="commercial_event">Commercial Event</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-stone-700 dark:text-stone-300 mb-1">
                  Description
                </label>
                <textarea
                  value={formData.event_description}
                  onChange={(e) => setFormData({ ...formData, event_description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-stone-300 dark:border-stone-600 rounded-lg bg-white dark:bg-stone-800 text-ink dark:text-paper"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-stone-700 dark:text-stone-300 mb-1">
                  Affected Assets (comma-separated)
                </label>
                <input
                  type="text"
                  value={formData.expected_impact}
                  onChange={(e) => setFormData({ ...formData, expected_impact: e.target.value })}
                  placeholder="e.g., main_website,ecommerce,streaming"
                  className="w-full px-3 py-2 border border-stone-300 dark:border-stone-600 rounded-lg bg-white dark:bg-stone-800 text-ink dark:text-paper"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-stone-700 dark:text-stone-300 mb-1">
                  Impact Magnitude
                </label>
                <div className="flex gap-4">
                  {["high", "medium", "low"].map((mag) => (
                    <label key={mag} className="flex items-center gap-2">
                      <input
                        type="radio"
                        value={mag}
                        checked={formData.impact_magnitude === mag}
                        onChange={(e) =>
                          setFormData({ ...formData, impact_magnitude: e.target.value as ImpactMagnitude })
                        }
                        className="text-sport-blue-600"
                      />
                      <span className="text-sm capitalize text-stone-700 dark:text-stone-300">{mag}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={showAnomalyConfirmForm ? submitAnomalyConfirmation : handleAddEvent}
                className="flex-1 px-4 py-2 bg-sport-blue-600 text-white rounded-lg hover:bg-sport-blue-700 transition-colors font-semibold"
              >
                {showAnomalyConfirmForm ? "Confirm Event" : "Create Event"}
              </button>
              <button
                onClick={() => {
                  setShowAddForm(false);
                  setShowAnomalyConfirmForm(false);
                  setSelectedAnomaly(null);
                  setFormData({
                    event_date: "",
                    event_name: "",
                    event_category: "commercial_event",
                    event_description: "",
                    expected_impact: "",
                    impact_magnitude: "medium",
                  });
                }}
                className="flex-1 px-4 py-2 bg-stone-200 dark:bg-stone-700 text-stone-700 dark:text-stone-300 rounded-lg hover:bg-stone-300 dark:hover:bg-stone-600 transition-colors font-semibold"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-stone-900 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-xl font-headline text-ink dark:text-paper mb-4">Confirm Delete</h3>
            <p className="text-stone-700 dark:text-stone-300 mb-6">
              Are you sure you want to delete this event? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => handleDelete(deleteConfirm)}
                className="flex-1 px-4 py-2 bg-critical-600 text-white rounded-lg hover:bg-critical-700 transition-colors font-semibold"
              >
                Delete
              </button>
              <button
                onClick={() => setDeleteConfirm(null)}
                className="flex-1 px-4 py-2 bg-stone-200 dark:bg-stone-700 text-stone-700 dark:text-stone-300 rounded-lg hover:bg-stone-300 dark:hover:bg-stone-600 transition-colors font-semibold"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
