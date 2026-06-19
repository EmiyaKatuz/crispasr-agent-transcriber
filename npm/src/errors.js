export class InstallerError extends Error {
  constructor(message, code = "installer_error", details = {}) {
    super(message);
    this.name = "InstallerError";
    this.code = code;
    this.details = details;
  }

  toJSON() {
    return {
      code: this.code,
      message: this.message,
      details: this.details,
    };
  }
}
