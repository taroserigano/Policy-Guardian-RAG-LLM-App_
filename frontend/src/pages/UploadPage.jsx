/**
 * Upload page for document management.
 */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, CheckCircle, AlertCircle, ArrowRight } from "lucide-react";
import FileDrop from "../components/FileDrop";
import { useUploadDocument, useDocuments } from "../hooks/useApi";

export default function UploadPage() {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null);

  const uploadMutation = useUploadDocument();
  const { data: documents } = useDocuments();

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setUploadStatus(null);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploadStatus({
        type: "loading",
        message: "Uploading and indexing...",
      });

      const result = await uploadMutation.mutateAsync(selectedFile);

      setUploadStatus({
        type: "success",
        message: `Successfully uploaded: ${result.filename}`,
      });

      // Reset after 2 seconds
      setTimeout(() => {
        setSelectedFile(null);
        setUploadStatus(null);
      }, 2000);
    } catch (error) {
      setUploadStatus({
        type: "error",
        message: error.response?.data?.detail || "Failed to upload document",
      });
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Upload Documents
        </h1>
        <p className="text-gray-600">
          Upload policy, compliance, or legal documents (PDF or TXT) to make
          them searchable.
        </p>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
        <FileDrop onFileSelect={handleFileSelect} />

        {selectedFile && !uploadStatus && (
          <div className="mt-6">
            <button
              onClick={handleUpload}
              disabled={uploadMutation.isPending}
              className="w-full flex items-center justify-center px-6 py-3 bg-primary-600 text-white font-medium rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Upload className="h-5 w-5 mr-2" />
              {uploadMutation.isPending
                ? "Uploading..."
                : "Upload & Index Document"}
            </button>
          </div>
        )}

        {/* Status Messages */}
        {uploadStatus && (
          <div
            className={`mt-6 p-4 rounded-md ${
              uploadStatus.type === "success"
                ? "bg-green-50 border border-green-200"
                : uploadStatus.type === "error"
                ? "bg-red-50 border border-red-200"
                : "bg-blue-50 border border-blue-200"
            }`}
          >
            <div className="flex items-center">
              {uploadStatus.type === "success" && (
                <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
              )}
              {uploadStatus.type === "error" && (
                <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
              )}
              {uploadStatus.type === "loading" && (
                <div className="h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-2" />
              )}
              <p
                className={`text-sm font-medium ${
                  uploadStatus.type === "success"
                    ? "text-green-800"
                    : uploadStatus.type === "error"
                    ? "text-red-800"
                    : "text-blue-800"
                }`}
              >
                {uploadStatus.message}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            Uploaded Documents ({documents?.length || 0})
          </h2>

          {documents && documents.length > 0 && (
            <button
              onClick={() => navigate("/chat")}
              className="flex items-center text-sm font-medium text-primary-600 hover:text-primary-700"
            >
              Go to Chat
              <ArrowRight className="h-4 w-4 ml-1" />
            </button>
          )}
        </div>

        {documents && documents.length > 0 ? (
          <div className="space-y-3">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="p-4 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">
                      {doc.filename}
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">
                      Uploaded: {new Date(doc.created_at).toLocaleString()}
                    </p>
                    {doc.preview_text && (
                      <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                        {doc.preview_text}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-center text-gray-500 py-8">
            No documents uploaded yet. Upload your first document above.
          </p>
        )}
      </div>
    </div>
  );
}
