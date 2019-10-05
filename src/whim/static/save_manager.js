class SaveManager {
  constructor(editor, api_client, onChange, onSave) {
    this._editor = editor;
    this._api_client = api_client;
    this._clientOnChange = onChange;
    this._clientOnSave = onSave;
    this._saved_content = '';
    this._unsaved_changes = false;
    editor.on('change', () => this._onChange());
  }
  async open(file_path) {
    let content = await this._api_client.readFile(file_path);
    this._saved_content = content;
    this._editor.session.setMode(modelist.getModeForPath(file_path).mode);
    this._editor.setValue(content, -1);
  }
  async save(file_path) {
    let content = editor.getValue();
    try {
      await this._api_client.writeFile(file_path, content);
    } catch {
      alert('Failed to save!');
      return false;
    }
    this._saved_content = content;
    this._checkSaved();
  }
  async _onChange() {
    if (!this._unsaved_changes) {
      this._checkSaved();
    } else {
      // Check if all changes have been undone
      // 1 second after the latest change
      clearTimeout(this._scheduledCheckSaved);
      this._scheduledCheckSaved = setTimeout(
        () => this._checkSaved(),
        1000
      );
    }
  }
  _checkSaved() {
    let content = editor.getValue();
    if (content === this._saved_content) {
      if (this._unsaved_changes) {
        this._unsaved_changes = false;
        this._clientOnSave();
      }
    } else {
      if (!this._unsaved_changes) {
        this._unsaved_changes = true;
        this._clientOnChange();
      }
    }
  }
}
