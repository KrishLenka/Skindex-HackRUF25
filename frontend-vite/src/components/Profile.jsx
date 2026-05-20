import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { User, Save, LogOut, ChevronDown, History, X, ChevronRight, AlertTriangle } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const AGE_GROUPS = ["<18", "18-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"];

const SEX_OPTIONS = [
  { value: "male",                 label: "Male" },
  { value: "female",               label: "Female" },
  { value: "other_or_unspecified", label: "Other / Unspecified" },
];

const FITZPATRICK_OPTIONS = [
  { value: "NEVER_TANS",           label: "Type I — Always burns, never tans" },
  { value: "TANS_MINIMALLY",       label: "Type II — Burns easily, tans minimally" },
  { value: "TANS_UNIFORMLY",       label: "Type III — Burns moderately, tans uniformly" },
  { value: "ALWAYS_TANS_WELL",     label: "Type IV — Burns minimally, always tans well" },
  { value: "TANS_EASILY",          label: "Type V — Rarely burns, tans easily" },
  { value: "ALWAYS_TANS",          label: "Type VI — Never burns, always tans deeply" },
  { value: "NONE_OF_THE_ABOVE_OR_UNKNOWN", label: "None of the above / Unknown" },
];

const ETHNICITY_OPTIONS = [
  { value: "AMERICAN_INDIAN_OR_ALASKA_NATIVE",    label: "American Indian or Alaska Native" },
  { value: "ASIAN",                               label: "Asian" },
  { value: "BLACK_OR_AFRICAN_AMERICAN",           label: "Black or African American" },
  { value: "HISPANIC_LATINO_OR_SPANISH_ORIGIN",   label: "Hispanic, Latino, or Spanish Origin" },
  { value: "MIDDLE_EASTERN_OR_NORTH_AFRICAN",     label: "Middle Eastern or North African" },
  { value: "NATIVE_HAWAIIAN_OR_PACIFIC_ISLANDER", label: "Native Hawaiian or Pacific Islander" },
  { value: "WHITE",                               label: "White" },
  { value: "TWO_OR_MORE",                         label: "Two or More Races" },
  { value: "OTHER_RACE",                          label: "Other Race" },
  { value: "PREFER_NOT_TO_ANSWER",                label: "Prefer Not to Answer" },
];

const TEXTURE_OPTIONS = [
  { value: "TEXTURE_UNSPECIFIED", label: "Unspecified" },
  { value: "RAISED_OR_BUMPY",     label: "Raised or Bumpy" },
  { value: "FLAT",                label: "Flat" },
  { value: "ROUGH_OR_FLAKY",      label: "Rough or Flaky" },
  { value: "FLUID_FILLED",        label: "Fluid Filled" },
];

/**
 * A reusable controlled select dropdown layout element for the profile form.
 *
 * @param {Object} props - React props.
 * @param {string} props.label - Human-readable label for the field.
 * @param {string} props.value - The currently selected internal value.
 * @param {Function} props.onChange - State mutator callback function.
 * @param {Array<{value: string, label: string}> | Array<string>} props.options - Selectable options.
 * @param {string} props.placeholder - The default unbound prompt text.
 * @returns {JSX.Element} Select form control block.
 */
function SelectField({ label, value, onChange, options, placeholder }) {
  return (
    <div>
      <label className="block text-sm font-medium text-rose-800 mb-1">{label}</label>
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full appearance-none rounded-lg border border-rose-200 bg-white px-3 py-2.5 pr-8 text-sm text-rose-900 focus:outline-none focus:ring-2 focus:ring-rose-400"
        >
          <option value="">{placeholder}</option>
          {options.map((o) => (
            <option key={o.value ?? o} value={o.value ?? o}>
              {o.label ?? o}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-2.5 top-3 w-4 h-4 text-rose-400" />
      </div>
    </div>
  );
}

const SEVERITY_COLORS = {
  Low:      "bg-green-100 text-green-800 border-green-200",
  Moderate: "bg-amber-100 text-amber-800 border-amber-200",
  High:     "bg-red-100 text-red-800 border-red-200",
};

/**
 * The authenticated user's dashboard view.
 * Handles updating of their demographic profile and rendering of past upload history.
 *
 * @returns {JSX.Element | null} The Profile component or null if no user is authenticated.
 */
export default function Profile() {
  const { user, token, updateProfile, logout } = useAuth();
  const navigate                               = useNavigate();

  // --- Demographics form state ---
  const [form, setForm]       = useState({
    name:         "",
    age_group:    "",
    sex_at_birth: "",
    fitzpatrick:  "",
    ethnicity:    "",
    texture:      "",
  });
  const [busy, setBusy]       = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError]     = useState("");

  // --- Scan history state ---
  const [scans, setScans]               = useState([]);
  const [scansLoading, setScansLoading] = useState(false);
  const [selectedScan, setSelectedScan] = useState(null);   // summary (no image)
  const [scanDetail, setScanDetail]     = useState(null);   // full detail with image
  const [detailLoading, setDetailLoading] = useState(false);
  const [deleting, setDeleting]           = useState(false);

  useEffect(() => {
    if (user) {
      setForm({
        name:         user.name         || "",
        age_group:    user.age_group    || "",
        sex_at_birth: user.sex_at_birth || "",
        fitzpatrick:  user.fitzpatrick  || "",
        ethnicity:    user.ethnicity    || "",
        texture:      user.texture      || "",
      });
    }
  }, [user]);

  const fetchScans = useCallback(() => {
    if (!token) return;
    setScansLoading(true);
    fetch("/api/scans", { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.json())
      .then((data) => setScans(data.scans || []))
      .catch(console.error)
      .finally(() => setScansLoading(false));
  }, [token]);

  useEffect(() => {
    fetchScans();
  }, [fetchScans]);

  /**
   * Opens the detail modal for a given scan and fetches full scan JSON blob data.
   *
   * @param {Object} scan - The slim summary scan object to expand.
   */
  const openScan = (scan) => {
    setSelectedScan(scan);
    setScanDetail(null);
    setDetailLoading(true);
    fetch(`/api/scans/${scan.id}`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.json())
      .then((data) => setScanDetail(data.scan || null))
      .catch(console.error)
      .finally(() => setDetailLoading(false));
  };

  /**
   * Closes the scan detail modal and resets state.
   */
  const closeModal = () => {
    setSelectedScan(null);
    setScanDetail(null);
  };

  /**
   * Initiates a delete request for a specific scan.
   * 
   * @param {string|number} scanId - The ID of the scan.
   */
  const deleteScan = async (scanId) => {
    if (!window.confirm("Delete this scan? This cannot be undone.")) return;
    setDeleting(true);
    try {
      await fetch(`/api/scans/${scanId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      closeModal();
      fetchScans();
    } catch (err) {
      console.error(err);
    } finally {
      setDeleting(false);
    }
  };

  /**
   * A curried state setter hook generator.
   *
   * @param {string} field - The demographic profile string key.
   * @returns {Function} A setter function for that field.
   */
  const set = (field) => (value) => setForm((prev) => ({ ...prev, [field]: value }));

  /**
   * Dispatches the local profile state payload securely to the backend for update.
   *
   * @param {React.FormEvent} e - Form event action.
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess(false);
    setBusy(true);
    try {
      await updateProfile(form);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  /**
   * Invokes the auth context's token wipe handler, effectively concluding the active session.
   */
  const handleLogout = () => {
    logout();
    navigate("/");
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-50 via-orange-50 to-amber-100 py-10 px-4">
      <div className="mx-auto max-w-2xl">
        {/* Header card */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-rose-200/60 p-6 mb-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-rose-100 flex items-center justify-center shadow-inner">
              <User className="w-7 h-7 text-rose-600" />
            </div>
            <div>
              <p className="text-lg font-bold text-rose-900">{user.name}</p>
              <p className="text-sm text-rose-600">{user.email}</p>
              {user.created_at && (
                <p className="text-xs text-rose-400 mt-0.5">
                  Member since {new Date(user.created_at).toLocaleDateString()}
                </p>
              )}
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-sm text-rose-600 hover:text-rose-800 font-medium transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>
        </div>

        {/* Demographics form */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-rose-200/60 p-8 mb-6">
          <h2 className="text-xl font-bold text-rose-900 mb-1">Your Health Profile</h2>
          <p className="text-sm text-rose-600/80 mb-6">
            This information helps personalise your skin analysis results.
          </p>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-rose-800 mb-1">Full name</label>
              <input
                type="text"
                required
                value={form.name}
                onChange={(e) => set("name")(e.target.value)}
                placeholder="Your name"
                className="w-full rounded-lg border border-rose-200 bg-white px-3 py-2.5 text-sm text-rose-900 placeholder-rose-400 focus:outline-none focus:ring-2 focus:ring-rose-400"
              />
            </div>

            <SelectField
              label="Age group"
              value={form.age_group}
              onChange={set("age_group")}
              options={AGE_GROUPS.map((a) => ({ value: a, label: a }))}
              placeholder="Select age group"
            />
            <SelectField
              label="Sex at birth"
              value={form.sex_at_birth}
              onChange={set("sex_at_birth")}
              options={SEX_OPTIONS}
              placeholder="Select sex at birth"
            />
            <SelectField
              label="Fitzpatrick skin type"
              value={form.fitzpatrick}
              onChange={set("fitzpatrick")}
              options={FITZPATRICK_OPTIONS}
              placeholder="Select skin type"
            />
            <SelectField
              label="Ethnicity"
              value={form.ethnicity}
              onChange={set("ethnicity")}
              options={ETHNICITY_OPTIONS}
              placeholder="Select ethnicity"
            />
            <SelectField
              label="Skin texture"
              value={form.texture}
              onChange={set("texture")}
              options={TEXTURE_OPTIONS}
              placeholder="Select texture"
            />

            <button
              type="submit"
              disabled={busy}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-rose-600 px-4 py-2.5 text-sm font-semibold text-white shadow hover:bg-rose-700 focus:outline-none focus:ring-2 focus:ring-rose-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Save className="w-4 h-4" />
              {busy ? "Saving…" : "Save profile"}
            </button>

            {success && (
              <div className="rounded-lg bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-700 text-center font-medium">
                ✓ Profile updated successfully.
              </div>
            )}
          </form>
        </div>

        {/* ---- Scan History ---- */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-rose-200/60 p-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <History className="w-5 h-5 text-rose-600" />
              <h2 className="text-xl font-bold text-rose-900">Scan History</h2>
            </div>
            <span className="text-sm text-rose-500">{scans.length} scan{scans.length !== 1 ? "s" : ""}</span>
          </div>

          {scansLoading && (
            <p className="text-sm text-rose-400 text-center py-6">Loading scans…</p>
          )}

          {!scansLoading && scans.length === 0 && (
            <div className="text-center py-8 text-rose-400">
              <AlertTriangle className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No scans yet. Analyse an image to get started.</p>
            </div>
          )}

          {!scansLoading && scans.length > 0 && (
            <div className="space-y-3">
              {scans.map((scan) => (
                <button
                  key={scan.id}
                  onClick={() => openScan(scan)}
                  className="w-full text-left flex items-center justify-between gap-4 rounded-xl border border-rose-100 bg-rose-50/60 hover:bg-rose-100/70 px-4 py-3.5 transition-colors group"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-rose-900 text-sm">{scan.condition || "Unknown condition"}</span>
                      {scan.severity && (
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${SEVERITY_COLORS[scan.severity] || "bg-gray-100 text-gray-700 border-gray-200"}`}>
                          {scan.severity}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-rose-500">
                      {scan.body_part && <span>{scan.body_part.replace(/_/g, " ")}</span>}
                      {scan.confidence != null && <span>{scan.confidence}% confidence</span>}
                      <span>{new Date(scan.created_at).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })}</span>
                    </div>
                    {scan.symptoms?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {scan.symptoms.slice(0, 3).map((s) => (
                          <span key={s} className="text-xs bg-rose-100 text-rose-700 rounded px-1.5 py-0.5">{s.replace(/_/g, " ")}</span>
                        ))}
                        {scan.symptoms.length > 3 && (
                          <span className="text-xs text-rose-400">+{scan.symptoms.length - 3} more</span>
                        )}
                      </div>
                    )}
                  </div>
                  <ChevronRight className="w-4 h-4 text-rose-400 flex-shrink-0 group-hover:translate-x-0.5 transition-transform" />
                </button>
              ))}
            </div>
          )}
        </div>

        <p className="text-center text-xs text-rose-400 mt-4">
          Your information is stored securely and is never shared with third parties.
        </p>
      </div>

      {/* ---- Scan Detail Modal ---- */}
      {selectedScan && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={closeModal}
        >
          <div
            className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal header */}
            <div className="sticky top-0 bg-white border-b border-rose-100 px-6 py-4 flex items-center justify-between rounded-t-2xl">
              <h3 className="font-bold text-rose-900 text-lg">Scan Details</h3>
              <button onClick={closeModal} className="text-rose-400 hover:text-rose-700 transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="px-6 py-5 space-y-5">
              {detailLoading && (
                <p className="text-sm text-rose-400 text-center py-6">Loading details…</p>
              )}

              {!detailLoading && scanDetail && (
                <>
                  {/* Image */}
                  {scanDetail.image_b64 && (
                    <div className="rounded-xl overflow-hidden border border-rose-100">
                      <img
                        src={scanDetail.image_b64}
                        alt="Scanned skin area"
                        className="w-full object-cover max-h-72"
                      />
                    </div>
                  )}

                  {/* Date */}
                  <p className="text-xs text-rose-400">
                    Scanned on {new Date(scanDetail.created_at).toLocaleString()}
                  </p>

                  {/* Diagnosis summary */}
                  <div className="rounded-xl bg-rose-50 border border-rose-100 p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-rose-900">{scanDetail.condition || "Unknown"}</span>
                      {scanDetail.severity && (
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${SEVERITY_COLORS[scanDetail.severity] || "bg-gray-100 text-gray-700 border-gray-200"}`}>
                          {scanDetail.severity}
                        </span>
                      )}
                    </div>
                    {scanDetail.confidence != null && (
                      <p className="text-xs text-rose-500">{scanDetail.confidence}% confidence</p>
                    )}
                  </div>

                  {/* Context info */}
                  <div className="space-y-2">
                    {scanDetail.body_part && (
                      <div>
                        <span className="text-xs font-medium text-rose-700 uppercase tracking-wide">Body part</span>
                        <p className="text-sm text-rose-900 mt-0.5">{scanDetail.body_part.replace(/_/g, " ")}</p>
                      </div>
                    )}
                    {scanDetail.symptoms?.length > 0 && (
                      <div>
                        <span className="text-xs font-medium text-rose-700 uppercase tracking-wide">Symptoms</span>
                        <div className="flex flex-wrap gap-1.5 mt-1">
                          {scanDetail.symptoms.map((s) => (
                            <span key={s} className="text-xs bg-rose-100 text-rose-700 rounded px-2 py-0.5">{s.replace(/_/g, " ")}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {scanDetail.description && (
                      <div>
                        <span className="text-xs font-medium text-rose-700 uppercase tracking-wide">Description</span>
                        <p className="text-sm text-rose-900 mt-0.5">{scanDetail.description}</p>
                      </div>
                    )}
                  </div>

                  {/* Recommendations */}
                  {scanDetail.recommendations?.length > 0 && (
                    <div>
                      <span className="text-xs font-medium text-rose-700 uppercase tracking-wide">AI Recommendations</span>
                      <ul className="mt-2 space-y-1.5">
                        {scanDetail.recommendations.map((rec, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-rose-900">
                            <span className="mt-1 w-1.5 h-1.5 rounded-full bg-rose-400 flex-shrink-0" />
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <button
                    onClick={() => deleteScan(scanDetail.id)}
                    disabled={deleting}
                    className="mt-4 w-full py-2 rounded-lg text-sm font-medium bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-50 transition-colors"
                  >
                    {deleting ? "Deleting…" : "Delete this scan"}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

