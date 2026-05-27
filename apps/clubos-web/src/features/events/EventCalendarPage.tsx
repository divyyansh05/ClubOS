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
import { ScreenGuide } from "../../components/ui/ScreenGuide";

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

// Returns Tailwind classes for a magnitude badge — aligned to design system tokens
const getMagnitudeStyles = (magnitude: ImpactMagnitude): string => {
  switch (magnitude) {
    case "high":
      return "border-critical-600 bg-critical-50 dark:bg-stone-900 text-critical-700 dark:text-critical-300";
    case "medium":
      return "border-warning-600 bg-warning-50 dark:bg-stone-900 text-warning-700 dark:text-warning-300";
    case "low":
      return "border-info-600 bg-info-50 dark:bg-stone-900 text-info-700 dark:text-info-300";
    default:
      return "border-stone-300 bg-stone-50 dark:bg-stone-800 text-stone-700 dark:text-stone-300";
  }
};

// ─── Shared style tokens (newsprint aesthetic) ─────────────────────────────
const pillBase =
  "font-mono text-xs uppercase tracking-wider border-2 px-4 py-2 transition-colors duration-150";
const pillActive =
  "border-ink bg-ink text-paper dark:border-stone-300 dark:bg-stone-300 dark:text-stone-900";
const pillInactive =
  "border-stone-300 dark:border-stone-600 text-stone-600 dark:text-stone-400 hover:border-stone-500 dark:hover:border-stone-400 bg-paper dark:bg-stone-900";

const btnPrimary =
  "font-mono text-xs uppercase tracking-wider border-2 border-sport-blue-700 bg-sport-blue-600 text-white px-4 py-2 hover:bg-sport-blue-700 transition-colors duration-150";
const btnSecondary =
  "font-mono text-xs uppercase tracking-wider border-2 border-stone-300 dark:border-stone-600 text-stone-700 dark:text-stone-300 px-4 py-2 hover:border-stone-500 dark:hover:border-stone-400 transition-colors duration-150 bg-paper dark:bg-stone-900";
const btnDanger =
  "font-mono text-xs uppercase tracking-wider border-2 border-critical-600 bg-critical-600 text-white px-4 py-2 hover:bg-critical-700 hover:border-critical-700 transition-colors duration-150";

const formLabel =
  "block font-mono text-xs uppercase tracking-wider text-stone-600 dark:text-stone-400 mb-1";
const formInput =
  "w-full px-3 py-2 border-2 border-stone-300 dark:border-stone-600 bg-paper dark:bg-stone-800 text-ink dark:text-stone-100 font-body text-sm focus:border-ink dark:focus:border-stone-400 focus:outline-none transition-colors";

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
        Transfers:  ["player_signing", "player_departure", "transfer_window"],
        Matches:    ["match_result_win", "match_result_loss", "trophy_win", "trophy_loss"],
        Commercial: ["commercial_event"],
        Media:      ["media_event", "injury_news"],
      };
      const categories = categoryMap[selectedFilter] || [];
      setFilteredEvents(events.filter((e) => categories.includes(e.event_category)));
    }
  };

  const handleAddEvent = async () => {
    try {
      await createEvent(formData);
      setShowAddForm(false);
      resetForm();
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
      // Non-blocking — anomalies are supplementary
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
      const month = selectedAnomaly.month.substring(0, 7);
      await confirmAnomaly(month, {
        confirmed_name:     formData.event_name,
        confirmed_category: formData.event_category,
        description:        formData.event_description,
        impact_magnitude:   formData.impact_magnitude,
        affected_assets:    formData.expected_impact || "social_media",
      });
      setShowAnomalyConfirmForm(false);
      setSelectedAnomaly(null);
      resetForm();
      loadEvents();
      loadAnomalies();
    } catch (err) {
      console.error(err);
      alert("Failed to confirm anomaly");
    }
  };

  const handleDismissAnomaly = async (anomaly: SocialAnomaly) => {
    try {
      const month = anomaly.month.substring(0, 7);
      await dismissAnomaly(month);
      loadAnomalies();
    } catch (err) {
      console.error(err);
      alert("Failed to dismiss anomaly");
    }
  };

  const resetForm = () =>
    setFormData({
      event_date:        "",
      event_name:        "",
      event_category:    "commercial_event",
      event_description: "",
      expected_impact:   "",
      impact_magnitude:  "medium",
    });

  // Pre-fill form from anomaly when opening confirm form
  useEffect(() => {
    if (selectedAnomaly && showAnomalyConfirmForm) {
      setFormData({
        event_date:        selectedAnomaly.month,
        event_name:        selectedAnomaly.candidate_event_name,
        event_category:    selectedAnomaly.candidate_category as EventCategory,
        event_description: `Auto-detected from social media anomaly. ${selectedAnomaly.metric} showed ${selectedAnomaly.z_score.toFixed(2)}-sigma deviation in ${selectedAnomaly.month.substring(0, 7)}.`,
        expected_impact:   "social_media",
        impact_magnitude:  (selectedAnomaly.confidence_level === "high" ? "high" : "medium") as ImpactMagnitude,
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

  // ── Loading / error ───────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="p-8 max-w-screen-xl mx-auto">
        <div className="font-mono text-xs uppercase tracking-widest text-stone-500 dark:text-stone-400">
          Loading events…
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 max-w-screen-xl mx-auto">
        <div className="font-mono text-sm text-critical-600 dark:text-critical-dark">{error}</div>
      </div>
    );
  }

  return (
    <div className="max-w-screen-xl mx-auto px-6 py-8">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="mb-8 border-b-2 border-ink dark:border-stone-700 pb-6">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h1 className="font-headline text-4xl md:text-5xl tracking-tight text-ink dark:text-stone-100">
              Event Calendar
            </h1>
            <p className="font-body text-base text-stone-600 dark:text-stone-400 mt-1">
              Track real-world events that impact your digital metrics. Events appear as
              annotations on metric charts to provide context for KPI movements.
            </p>
          </div>
          <button
            id="add-event-btn"
            onClick={() => setShowAddForm(true)}
            className={btnPrimary}
          >
            + Add Event
          </button>
        </div>
      </div>

      {/* ── Social Anomalies Panel (V1.6.5) ────────────────────────────────── */}
      {!anomaliesLoading && anomalies.length > 0 && (
        <div className="mb-8 border-2 border-warning-600 dark:border-warning-dark bg-warning-50 dark:bg-stone-900 p-6">
          <h2 className="font-headline text-2xl text-ink dark:text-stone-100 mb-1">
            Social Anomalies — Pending Confirmation
          </h2>
          <p className="font-body text-sm text-stone-700 dark:text-stone-300 mb-6">
            These months show unusual social media activity. Confirm if they correspond to a
            real-world event to add context across all ClubOS metrics.
          </p>
          <div className="space-y-4">
            {anomalies.map((anomaly, idx) => {
              const month_display = new Date(anomaly.month).toLocaleDateString("en-US", {
                month: "short",
                year:  "numeric",
              });
              return (
                <div
                  key={idx}
                  className="bg-paper dark:bg-stone-800 border-2 border-stone-300 dark:border-stone-700 p-5"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2 mb-3">
                        {/* Month badge */}
                        <span className="font-mono text-xs uppercase tracking-wider px-3 py-1 border-2 border-ink bg-ink text-paper dark:border-stone-300 dark:bg-stone-300 dark:text-stone-900">
                          {month_display}
                        </span>
                        {/* Confidence badge */}
                        <span
                          className={`font-mono text-xs uppercase tracking-wider px-3 py-1 border ${
                            anomaly.confidence_level === "high"
                              ? "border-critical-600 text-critical-700 dark:text-critical-300"
                              : anomaly.confidence_level === "medium"
                              ? "border-warning-600 text-warning-700 dark:text-warning-300"
                              : "border-info-600 text-info-700 dark:text-info-300"
                          }`}
                        >
                          {anomaly.confidence_level} confidence
                        </span>
                      </div>
                      <p className="font-body text-sm text-stone-700 dark:text-stone-300 mb-2">
                        <strong className="text-ink dark:text-stone-100">Detected pattern:</strong>{" "}
                        {anomaly.metric.replace(/_/g, " ")} was{" "}
                        {Math.abs(anomaly.z_score).toFixed(1)} standard deviations{" "}
                        {anomaly.direction === "spike" ? "above" : "below"} average —{" "}
                        {anomaly.direction} detected.
                      </p>
                      <p className="font-body text-sm text-stone-700 dark:text-stone-300">
                        <strong className="text-ink dark:text-stone-100">
                          {getCategoryIcon(anomaly.candidate_category as EventCategory)} Possible:
                        </strong>{" "}
                        {anomaly.likely_cause.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                      </p>
                    </div>
                    <div className="flex flex-col gap-2 flex-shrink-0">
                      <button
                        id={`confirm-anomaly-${idx}`}
                        onClick={() => handleConfirmAnomaly(anomaly)}
                        className={btnPrimary}
                      >
                        Confirm as Event
                      </button>
                      <button
                        id={`dismiss-anomaly-${idx}`}
                        onClick={() => handleDismissAnomaly(anomaly)}
                        className={btnSecondary}
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

      {/* ── Category Filters ────────────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-2 mb-8">
        {CATEGORIES_DEDUPE.map((category) => (
          <button
            key={category}
            id={`filter-${category.toLowerCase()}`}
            onClick={() => setSelectedFilter(category)}
            className={`${pillBase} ${
              selectedFilter === category ? pillActive : pillInactive
            }`}
          >
            {category}
          </button>
        ))}
      </div>

      {/* ── Event List ──────────────────────────────────────────────────────── */}
      {filteredEvents.length === 0 ? (
        <div className="text-center py-20 border-2 border-dashed border-stone-300 dark:border-stone-700">
          <p className="font-mono text-xs uppercase tracking-widest text-stone-400 dark:text-stone-500">
            No events registered for this period
          </p>
        </div>
      ) : (
        <div className="space-y-10">
          {sortedMonths.map((month) => (
            <div key={month}>
              {/* Month group header — newspaper section divider */}
              <div className="flex items-center gap-4 mb-4">
                <h2 className="font-headline text-2xl text-ink dark:text-stone-100">
                  {new Date(month + "-15").toLocaleDateString("en-US", {
                    month: "long",
                    year:  "numeric",
                  })}
                </h2>
                <div className="flex-1 h-px bg-stone-300 dark:bg-stone-700" />
                <span className="font-mono text-xs uppercase tracking-widest text-stone-400 dark:text-stone-500">
                  {groupedEvents[month].length} event{groupedEvents[month].length !== 1 ? "s" : ""}
                </span>
              </div>

              <div className="space-y-4">
                {groupedEvents[month]
                  .sort((a, b) => b.event_date.localeCompare(a.event_date))
                  .map((event) => (
                    <div
                      key={event.event_id}
                      className="bg-paper dark:bg-stone-800 border-2 border-ink dark:border-stone-700 p-6 transition-shadow duration-200 hover:shadow-sport"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-4 flex-1">
                          {/* Category icon box */}
                          <div className="flex-shrink-0 w-12 h-12 border-2 border-ink dark:border-stone-600 bg-stone-100 dark:bg-stone-900 flex items-center justify-center text-2xl">
                            {getCategoryIcon(event.event_category)}
                          </div>

                          <div className="flex-1">
                            <div className="flex flex-wrap items-center gap-2 mb-1">
                              <h3 className="font-headline text-xl text-ink dark:text-stone-100">
                                {event.event_name}
                              </h3>
                              <span
                                className={`font-mono text-xs uppercase tracking-wider px-2 py-0.5 border ${getMagnitudeStyles(
                                  event.impact_magnitude
                                )}`}
                              >
                                {event.impact_magnitude}
                              </span>
                            </div>

                            <p className="font-mono text-xs text-stone-400 dark:text-stone-500 mb-2 uppercase tracking-wider">
                              {new Date(event.event_date).toLocaleDateString("en-US", {
                                weekday: "short",
                                day:     "numeric",
                                month:   "long",
                                year:    "numeric",
                              })}
                            </p>

                            <p className="font-body text-sm text-stone-700 dark:text-stone-300 mb-3 leading-relaxed">
                              {event.event_description}
                            </p>

                            {event.affected_assets.length > 0 && (
                              <div className="flex flex-wrap gap-2">
                                {event.affected_assets.map((asset) => (
                                  <span
                                    key={asset}
                                    className="font-mono text-[10px] uppercase tracking-widest px-2 py-1 border border-stone-300 dark:border-stone-600 text-stone-500 dark:text-stone-400 bg-stone-50 dark:bg-stone-900"
                                  >
                                    {asset}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>

                        <button
                          id={`delete-${event.event_id}`}
                          onClick={() => setDeleteConfirm(event.event_id)}
                          className="font-mono text-xs uppercase tracking-wider text-critical-600 dark:text-critical-dark hover:text-critical-700 dark:hover:text-critical-light border border-transparent hover:border-critical-300 dark:hover:border-critical-700 px-2 py-1 transition-colors flex-shrink-0"
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

      {/* ── Add Event / Anomaly Confirm Modal ──────────────────────────────── */}
      {(showAddForm || showAnomalyConfirmForm) && (
        <div className="fixed inset-0 bg-ink/60 dark:bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="glass-modal max-w-2xl w-full max-h-[90vh] overflow-y-auto p-8 animate-scale-in">

            {/* Modal header */}
            <div className="flex items-center justify-between mb-6 border-b-2 border-stone-300 dark:border-stone-700 pb-4">
              <h2 className="font-headline text-2xl text-ink dark:text-stone-100">
                {showAnomalyConfirmForm ? "Confirm Social Anomaly as Event" : "Add New Event"}
              </h2>
              <button
                onClick={() => {
                  setShowAddForm(false);
                  setShowAnomalyConfirmForm(false);
                  setSelectedAnomaly(null);
                  resetForm();
                }}
                className="font-mono text-xs uppercase tracking-wider text-stone-500 dark:text-stone-400 hover:text-stone-700 dark:hover:text-stone-300 border border-stone-300 dark:border-stone-600 px-3 py-1 transition-colors"
              >
                ✕ Close
              </button>
            </div>

            {/* Anomaly context banner */}
            {showAnomalyConfirmForm && selectedAnomaly && (
              <div className="mb-6 border-l-4 border-warning-600 dark:border-warning-dark bg-warning-50 dark:bg-stone-900 p-4">
                <div className="font-mono text-xs uppercase tracking-wider text-warning-700 dark:text-warning-dark mb-1">
                  Auto-detected anomaly
                </div>
                <p className="font-body text-sm text-stone-700 dark:text-stone-300">
                  {selectedAnomaly.metric.replace(/_/g, " ")} showed{" "}
                  {Math.abs(selectedAnomaly.z_score).toFixed(1)}σ {selectedAnomaly.direction} in{" "}
                  {selectedAnomaly.month.substring(0, 7)}. Verify and confirm below.
                </p>
              </div>
            )}

            {/* Form fields */}
            <div className="space-y-5">
              <div>
                <label className={formLabel}>Event Name</label>
                <input
                  id="form-event-name"
                  type="text"
                  value={formData.event_name}
                  onChange={(e) => setFormData({ ...formData, event_name: e.target.value })}
                  className={formInput}
                  placeholder="e.g., El Clásico — Santiago Bernabéu"
                />
              </div>

              <div>
                <label className={formLabel}>Event Date</label>
                <input
                  id="form-event-date"
                  type="date"
                  value={formData.event_date}
                  onChange={(e) => setFormData({ ...formData, event_date: e.target.value })}
                  className={formInput}
                />
              </div>

              <div>
                <label className={formLabel}>Category</label>
                <select
                  id="form-event-category"
                  value={formData.event_category}
                  onChange={(e) =>
                    setFormData({ ...formData, event_category: e.target.value as EventCategory })
                  }
                  className={formInput}
                >
                  <option value="player_signing">Player Signing</option>
                  <option value="player_departure">Player Departure</option>
                  <option value="match_result_win">Match Result — Win</option>
                  <option value="match_result_loss">Match Result — Loss</option>
                  <option value="trophy_win">Trophy Win</option>
                  <option value="trophy_loss">Trophy Loss</option>
                  <option value="transfer_window">Transfer Window</option>
                  <option value="media_event">Media Event</option>
                  <option value="injury_news">Injury News</option>
                  <option value="commercial_event">Commercial Event</option>
                </select>
              </div>

              <div>
                <label className={formLabel}>Description</label>
                <textarea
                  id="form-event-description"
                  value={formData.event_description}
                  onChange={(e) =>
                    setFormData({ ...formData, event_description: e.target.value })
                  }
                  rows={3}
                  className={formInput}
                  placeholder="Brief description of the event and its expected commercial or social impact."
                />
              </div>

              <div>
                <label className={formLabel}>Affected Assets (comma-separated)</label>
                <input
                  id="form-affected-assets"
                  type="text"
                  value={formData.expected_impact}
                  onChange={(e) =>
                    setFormData({ ...formData, expected_impact: e.target.value })
                  }
                  placeholder="e.g., main_website, ecommerce, streaming"
                  className={formInput}
                />
              </div>

              <div>
                <label className={formLabel}>Impact Magnitude</label>
                <div className="flex gap-6">
                  {(["high", "medium", "low"] as ImpactMagnitude[]).map((mag) => (
                    <label
                      key={mag}
                      className="flex items-center gap-2 cursor-pointer"
                    >
                      <input
                        type="radio"
                        value={mag}
                        checked={formData.impact_magnitude === mag}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            impact_magnitude: e.target.value as ImpactMagnitude,
                          })
                        }
                        className="text-sport-blue-600"
                      />
                      <span
                        className={`font-mono text-xs uppercase tracking-wider px-3 py-1 border ${getMagnitudeStyles(mag)}`}
                      >
                        {mag}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* Modal actions */}
            <div className="flex gap-3 mt-8 pt-4 border-t-2 border-stone-200 dark:border-stone-700">
              <button
                id="form-submit-btn"
                onClick={showAnomalyConfirmForm ? submitAnomalyConfirmation : handleAddEvent}
                className={`flex-1 ${btnPrimary} py-3`}
              >
                {showAnomalyConfirmForm ? "Confirm Event" : "Create Event"}
              </button>
              <button
                id="form-cancel-btn"
                onClick={() => {
                  setShowAddForm(false);
                  setShowAnomalyConfirmForm(false);
                  setSelectedAnomaly(null);
                  resetForm();
                }}
                className={`flex-1 ${btnSecondary} py-3`}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Delete Confirmation Modal ─────────────────────────────────────── */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-ink/60 dark:bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="glass-modal max-w-md w-full p-8 animate-scale-in">
            <h3 className="font-headline text-2xl text-ink dark:text-stone-100 mb-3">
              Confirm Delete
            </h3>
            <p className="font-body text-sm text-stone-700 dark:text-stone-300 mb-8 leading-relaxed">
              Are you sure you want to delete this event? This action cannot be undone and will
              remove the annotation from all metric charts.
            </p>
            <div className="flex gap-3">
              <button
                id="confirm-delete-btn"
                onClick={() => handleDelete(deleteConfirm)}
                className={`flex-1 ${btnDanger} py-3`}
              >
                Delete Event
              </button>
              <button
                id="cancel-delete-btn"
                onClick={() => setDeleteConfirm(null)}
                className={`flex-1 ${btnSecondary} py-3`}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Screen Guide ─────────────────────────────────────────────────── */}
      <div className="mt-8" data-screen-guide>
        <ScreenGuide
          screenName="Event Calendar"
          sections={[
            {
              title: "What are events?",
              content:
                "Events are real-world occurrences — player transfers, match results, commercial partnerships, media coverage — that cause observable movements in your KPI metrics. Logging them gives ClubOS the context to explain why a metric moved.",
            },
            {
              title: "How events appear on charts",
              content:
                "Once logged, events appear as vertical annotations on the metric trend charts in the Command Center and Signals screens. This lets you immediately see whether a KPI spike or drop corresponds to a known event or is genuinely unexplained.",
            },
            {
              title: "Social Anomalies — what they are",
              content:
                "ClubOS automatically scans monthly social media data for statistical anomalies: months where engagement was significantly above or below the normal range (measured in standard deviations). When detected, an anomaly is shown here for you to confirm or dismiss.",
            },
            {
              title: "Confirming vs. dismissing an anomaly",
              content:
                "If a detected anomaly corresponds to a real event (e.g., a player farewell drove a spike), confirm it to add a permanent event record. If the anomaly is a data artefact or has no clear cause, dismiss it. Dismissed anomalies are removed from the pending list.",
            },
          ]}
        />
      </div>
    </div>
  );
}
