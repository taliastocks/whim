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

  async open(file_path, unsavedContent) {
    let content = await this._api_client.readFile(file_path);
    this._saved_content = content;
    this._editor.session.setMode(modelist.getModeForPath(file_path).mode);

    if (unsavedContent == null) {
      unsavedContent = content;
    }

    this._editor.setValue('', 0);
    this._editor.setValue(unsavedContent, -1);
    this._editor.session.getUndoManager().reset(); // Not meaningful to undo past file load.
    this._checkSaved();
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

  isUnsaved() {
    return this._unsaved_changes;
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
        this._clientOnChange(content);
        this._clientOnSave(content);
      }
    } else {
      this._unsaved_changes = true;
      this._clientOnChange(content);
    }
  }
}
