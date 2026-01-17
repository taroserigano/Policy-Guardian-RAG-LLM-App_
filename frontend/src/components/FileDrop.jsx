/**
 * File drop zone component for document upload.
 */
import { useState, useCallback } from "react";
import { Upload, File, AlertCircle, CheckCircle } from "lucide-react";

export default function FileDrop({
  onFileSelect,
  accept = ".pdf,.txt",
  maxSizeMB = 15,
}) {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const validateFile = (file) => {
    // Check file extension
    const ext = file.name.toLowerCase().match(/\.[^.]*$/)?.[0];
    const allowedExts = accept.split(",").map((e) => e.trim());

    if (!allowedExts.includes(ext)) {
      return `Invalid file type. Allowed: ${accept}`;
    }

    // Check file size
    const maxSize = maxSizeMB * 1024 * 1024;
    if (file.size > maxSize) {
      return `File too large. Maximum size: ${maxSizeMB}MB`;
    }

    return null;
  };

  const handleFile = useCallback(
    (file) => {
      setError(null);

      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        setSelectedFile(null);
        return;
      }

      setSelectedFile(file);
      onFileSelect(file);
    },
    [onFileSelect]
  );

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();

    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  return (
    <div className="w-full">
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? "border-primary-500 bg-primary-50"
            : error
            ? "border-red-300 bg-red-50"
            : selectedFile
            ? "border-green-300 bg-green-50"
            : "border-gray-300 bg-white hover:border-gray-400"
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          accept={accept}
          onChange={handleChange}
          className="hidden"
        />

        <label htmlFor="file-upload" className="cursor-pointer">
          <div className="flex flex-col items-center">
            {error ? (
              <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
            ) : selectedFile ? (
              <CheckCircle className="h-12 w-12 text-green-500 mb-4" />
            ) : (
              <Upload className="h-12 w-12 text-gray-400 mb-4" />
            )}

            {selectedFile ? (
              <div className="space-y-2">
                <div className="flex items-center justify-center text-green-700">
                  <File className="h-5 w-5 mr-2" />
                  <span className="font-medium">{selectedFile.name}</span>
                </div>
                <p className="text-sm text-gray-500">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
                <p className="text-sm text-gray-600">
                  Click or drag to replace
                </p>
              </div>
            ) : (
              <>
                <p className="text-lg font-medium text-gray-700 mb-2">
                  Drop your file here or click to browse
                </p>
                <p className="text-sm text-gray-500">
                  Supported: PDF, TXT (max {maxSizeMB}MB)
                </p>
              </>
            )}
          </div>
        </label>
      </div>

      {error && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-700 flex items-center">
            <AlertCircle className="h-4 w-4 mr-2" />
            {error}
          </p>
        </div>
      )}
    </div>
  );
}
