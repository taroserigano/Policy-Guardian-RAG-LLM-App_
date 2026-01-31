/**
 * Baggage Damage Refund Eligibility Checker Component
 * Specialized compliance checker for airline baggage damage claims
 */
import { useState, useRef } from "react";
import {
  Upload,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Loader2,
  FileImage,
  X,
  Info,
  Clock,
  Shield,
  FileText,
} from "lucide-react";
import toast from "react-hot-toast";
import { checkBaggageDamageEligibility } from "../api/client";

const DECISION_CONFIG = {
  eligible: {
    icon: CheckCircle,
    label: "Eligible for Refund",
    color: "text-green-400",
    bgColor: "bg-green-500/10",
    borderColor: "border-green-500/30",
  },
  not_eligible: {
    icon: XCircle,
    label: "Not Eligible",
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/30",
  },
  needs_review: {
    icon: AlertTriangle,
    label: "Needs Review",
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/10",
    borderColor: "border-yellow-500/30",
  },
};

export default function BaggageDamageChecker({ visionProvider = "openai" }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [reportedHours, setReportedHours] = useState("");
  const [isChecking, setIsChecking] = useState(false);
  const [result, setResult] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    console.log("File selected:", file);
    if (!file) return;

    // Validate file type - accept images and HEIC files (iPhone photos)
    const isImage = file.type.startsWith("image/");
    const isHEIC =
      file.name.toLowerCase().endsWith(".heic") ||
      file.name.toLowerCase().endsWith(".heif");

    if (!isImage && !isHEIC) {
      toast.error("Please select an image file (JPG, PNG, GIF, WEBP, HEIC)");
      return;
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error("Image must be less than 10MB");
      return;
    }

    setSelectedFile(file);
    setResult(null);
    console.log("File set successfully:", file.name);

    // Create preview
    const reader = new FileReader();
    reader.onload = (event) => {
      setPreviewUrl(event.target.result);
      console.log("Preview created");
    };
    reader.readAsDataURL(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    console.log("File dropped");

    const file = e.dataTransfer?.files?.[0];
    if (!file) return;

    // Validate file type - accept images and HEIC files (iPhone photos)
    const isImage = file.type.startsWith("image/");
    const isHEIC =
      file.name.toLowerCase().endsWith(".heic") ||
      file.name.toLowerCase().endsWith(".heif");

    if (!isImage && !isHEIC) {
      toast.error("Please select an image file (JPG, PNG, GIF, WEBP, HEIC)");
      return;
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error("Image must be less than 10MB");
      return;
    }

    setSelectedFile(file);
    setResult(null);
    console.log("File set successfully:", file.name);

    // Create preview
    const reader = new FileReader();
    reader.onload = (event) => {
      setPreviewUrl(event.target.result);
    };
    reader.readAsDataURL(file);
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleCheck = async () => {
    if (!selectedFile) {
      toast.error("Please select an image first");
      return;
    }

    setIsChecking(true);
    setResult(null);

    try {
      console.log("Starting eligibility check...", {
        fileName: selectedFile.name,
        fileSize: selectedFile.size,
        provider: visionProvider,
        reportedHours,
      });

      const hours = reportedHours ? parseInt(reportedHours, 10) : null;
      const eligibilityResult = await checkBaggageDamageEligibility(
        selectedFile,
        hours,
        visionProvider,
      );

      console.log("Eligibility result:", eligibilityResult);
      setResult(eligibilityResult);
      toast.success("Analysis complete");
    } catch (error) {
      console.error("Eligibility check failed:", error);
      console.error("Error details:", {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
      });
      toast.error(
        error.response?.data?.detail ||
          error.message ||
          "Failed to analyze image. Please try again.",
      );
    } finally {
      setIsChecking(false);
    }
  };

  const decisionConfig = result
    ? DECISION_CONFIG[result.decision] || DECISION_CONFIG.needs_review
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-violet-500/10 to-fuchsia-500/10 border border-violet-500/20 rounded-xl p-6">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-violet-500/20 rounded-xl">
            <Shield className="w-6 h-6 text-violet-400" />
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-2">
              Baggage Damage Refund Checker
            </h2>
            <p className="text-sm text-[var(--text-secondary)] mb-3">
              Upload a photo of your damaged checked hard-shell suitcase to
              determine refund eligibility based on airline policy.
            </p>
            <div className="flex items-start gap-2 text-xs text-[var(--text-muted)]">
              <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>
                The AI will assess damage type, severity, and policy compliance
                to determine if you're eligible for repair, replacement, or
                reimbursement.
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Section */}
      <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-6">
        <h3 className="text-sm font-medium text-[var(--text-primary)] mb-4">
          Upload Suitcase Photo
        </h3>

        {!selectedFile ? (
          <div
            onClick={() => fileInputRef.current?.click()}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className="relative border-2 border-dashed border-[var(--border-subtle)] rounded-xl p-12 text-center cursor-pointer hover:border-violet-500/50 hover:bg-violet-500/5 transition-all"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*,.heic,.heif"
              onChange={handleFileSelect}
              className="hidden"
            />
            <Upload className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" />
            <p className="text-sm font-medium text-[var(--text-primary)] mb-1">
              Click to upload or drag and drop
            </p>
            <p className="text-xs text-[var(--text-muted)]">
              PNG, JPG, GIF, WEBP, HEIC (max 10MB)
            </p>
          </div>
        ) : (
          <div className="relative bg-[var(--bg-tertiary)] rounded-xl p-4 border border-[var(--border-subtle)]">
            <div className="flex items-start gap-4">
              <div className="relative w-32 h-32 flex-shrink-0 rounded-lg overflow-hidden bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
                {previewUrl ? (
                  <img
                    src={previewUrl}
                    alt="Suitcase preview"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <FileImage className="w-8 h-8 text-[var(--text-muted)]" />
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[var(--text-primary)] truncate">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-[var(--text-muted)] mt-1">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <button
                onClick={handleClearFile}
                className="p-2 hover:bg-[var(--bg-secondary)] rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-[var(--text-muted)]" />
              </button>
            </div>
          </div>
        )}

        {/* Reporting Time Input */}
        <div className="mt-6">
          <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
            <Clock className="w-4 h-4 inline mr-1" />
            Reported within how many hours? (optional)
          </label>
          <input
            type="number"
            min="0"
            value={reportedHours}
            onChange={(e) => setReportedHours(e.target.value)}
            placeholder="e.g., 2 (hours since pickup/delivery)"
            className="w-full px-4 py-2 bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500/50 transition-all"
          />
          <p className="text-xs text-[var(--text-muted)] mt-2">
            Policy typically requires reporting within 24 hours of baggage
            pickup or delivery.
          </p>
        </div>

        {/* Check Button */}
        <button
          onClick={(e) => {
            console.log("Check button clicked!", { selectedFile, isChecking });
            e.preventDefault();
            handleCheck();
          }}
          disabled={!selectedFile || isChecking}
          className="w-full mt-6 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-violet-500 to-fuchsia-500 text-white font-semibold rounded-xl hover:from-violet-600 hover:to-fuchsia-600 focus:outline-none focus:ring-2 focus:ring-violet-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-violet-500/25"
        >
          {isChecking ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing Image...</span>
            </>
          ) : (
            <>
              <Shield className="w-5 h-5" />
              <span>Check Eligibility</span>
            </>
          )}
        </button>
      </div>

      {/* Results Section */}
      {result && decisionConfig && (
        <div className="space-y-6 animate-fadeIn">
          {/* Decision Badge */}
          <div
            className={`${decisionConfig.bgColor} ${decisionConfig.borderColor} border-2 rounded-xl p-6`}
          >
            <div className="flex items-center gap-3 mb-4">
              <decisionConfig.icon
                className={`w-8 h-8 ${decisionConfig.color}`}
              />
              <div>
                <h3 className={`text-lg font-semibold ${decisionConfig.color}`}>
                  {decisionConfig.label}
                </h3>
                <p className="text-sm text-[var(--text-muted)] mt-1">
                  Confidence: {(result.confidence * 100).toFixed(0)}%
                </p>
              </div>
            </div>
            <p className="text-sm text-[var(--text-secondary)]">
              {result.rationale}
            </p>
          </div>

          {/* Damage Assessment */}
          {result.damage_assessment && (
            <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-6">
              <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
                Damage Assessment
              </h4>
              <div className="space-y-3">
                <div>
                  <span className="text-xs text-[var(--text-muted)]">
                    Observed Damage:
                  </span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {result.damage_assessment.observed_damage_types?.map(
                      (type, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-full text-xs text-[var(--text-secondary)]"
                        >
                          {type.replace(/_/g, " ")}
                        </span>
                      ),
                    )}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-xs text-[var(--text-muted)]">
                      Severity:
                    </span>
                    <p className="text-sm font-medium text-[var(--text-primary)] mt-1">
                      Level {result.damage_assessment.severity} / 3
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-[var(--text-muted)]">
                      Functional Impact:
                    </span>
                    <p className="text-sm font-medium text-[var(--text-primary)] mt-1">
                      {String(
                        result.damage_assessment.functional_impairment,
                      ).replace(/_/g, " ")}
                    </p>
                  </div>
                </div>
                {result.damage_assessment.notes && (
                  <div>
                    <span className="text-xs text-[var(--text-muted)]">
                      Notes:
                    </span>
                    <p className="text-sm text-[var(--text-secondary)] mt-1">
                      {result.damage_assessment.notes}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Policy Application */}
          {result.policy_application && (
            <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-6">
              <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Policy Application
              </h4>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-xs text-[var(--text-muted)]">
                      Reporting Window:
                    </span>
                    <p
                      className={`text-sm font-medium mt-1 ${
                        result.policy_application.reporting_window_met === true
                          ? "text-green-400"
                          : result.policy_application.reporting_window_met ===
                              false
                            ? "text-red-400"
                            : "text-yellow-400"
                      }`}
                    >
                      {String(
                        result.policy_application.reporting_window_met,
                      ).replace(/_/g, " ")}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-[var(--text-muted)]">
                      Eligible Damage:
                    </span>
                    <p
                      className={`text-sm font-medium mt-1 ${
                        result.policy_application.eligible_damage_match === true
                          ? "text-green-400"
                          : result.policy_application.eligible_damage_match ===
                              false
                            ? "text-red-400"
                            : "text-yellow-400"
                      }`}
                    >
                      {String(
                        result.policy_application.eligible_damage_match,
                      ).replace(/_/g, " ")}
                    </p>
                  </div>
                </div>

                {result.policy_application.exclusion_triggers?.length > 0 &&
                  result.policy_application.exclusion_triggers[0] !==
                    "unknown" && (
                    <div>
                      <span className="text-xs text-[var(--text-muted)]">
                        Exclusion Triggers:
                      </span>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {result.policy_application.exclusion_triggers.map(
                          (trigger, idx) => (
                            <span
                              key={idx}
                              className="px-3 py-1 bg-red-500/10 border border-red-500/30 rounded-full text-xs text-red-400"
                            >
                              {trigger.replace(/_/g, " ")}
                            </span>
                          ),
                        )}
                      </div>
                    </div>
                  )}

                {result.policy_application.policy_references?.length > 0 && (
                  <div>
                    <span className="text-xs text-[var(--text-muted)]">
                      Policy References:
                    </span>
                    <div className="mt-2 space-y-2">
                      {result.policy_application.policy_references.map(
                        (ref, idx) => (
                          <div
                            key={idx}
                            className="bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-lg p-3"
                          >
                            <p className="text-xs font-medium text-violet-400">
                              {ref.section}
                            </p>
                            <p className="text-xs text-[var(--text-secondary)] mt-1 italic">
                              "{ref.quote}"
                            </p>
                          </div>
                        ),
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Next Steps */}
          {result.next_steps?.length > 0 && (
            <div className="bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-6">
              <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
                Recommended Next Steps
              </h4>
              <ul className="space-y-2">
                {result.next_steps.map((step, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-3 text-sm text-[var(--text-secondary)]"
                  >
                    <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded-full bg-violet-500/20 text-violet-400 text-xs font-medium mt-0.5">
                      {idx + 1}
                    </span>
                    <span className="flex-1">{step}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
