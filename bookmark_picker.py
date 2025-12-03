import tkinter as tk
from tkinter import ttk, messagebox
import plistlib
import os
import json

INPUT_FILE = os.path.expanduser("~/Library/Safari/Bookmarks.plist")
OUTPUT_FILE = "bookmarks.json"


class BookmarkPickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vlad's Bookmark Exporter")
        self.root.geometry("600x800")

        lbl = tk.Label(
            root,
            text="Expand folders and select specific links to export:",
            font=("Arial", 14),
        )
        lbl.pack(pady=10)

        frame = tk.Frame(root)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(frame, columns=("check",), selectmode="none")

        self.tree.column("#0", width=400, anchor="w")
        self.tree.heading("#0", text="Folder / Link Name")

        self.tree.column("check", width=50, anchor="center")
        self.tree.heading("check", text="Export?")

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.node_map = {}

        try:
            self.load_bookmarks()
        except PermissionError:
            messagebox.showerror(
                "Error",
                "Need Full Disk Access for Terminal/Python to read Safari Bookmarks.",
            )
            return

        btn = tk.Button(
            root,
            text="Export Selection to JSON",
            command=self.export_json,
            bg="#4CAF50",
            fg="black",
            font=("Arial", 12, "bold"),
        )
        btn.pack(pady=20, fill=tk.X, padx=20)

        self.tree.bind("<Button-1>", self.on_click)

    def load_bookmarks(self):
        with open(INPUT_FILE, "rb") as fp:
            plist = plistlib.load(fp)
            self.populate_tree("", plist.get("Children", []))

    def populate_tree(self, parent_id, children):
        for node in children:
            title = node.get(
                "Title", node.get("URIDictionary", {}).get("title", "Untitled")
            )
            node_type = node.get("WebBookmarkType")

            if node_type == "WebBookmarkTypeList" and "Children" in node:
                item_id = self.tree.insert(
                    parent_id, "end", text=f"📁 {title}", values=["[ ]"], open=False
                )
                self.node_map[item_id] = {
                    "type": "folder",
                    "title": title,
                    "children": node["Children"],
                    "checked": False,
                }
                self.populate_tree(item_id, node["Children"])

            elif node_type == "WebBookmarkTypeLeaf":
                url = node.get("URLString", "")
                if url:
                    item_id = self.tree.insert(
                        parent_id, "end", text=title, values=["[ ]"]
                    )
                    self.node_map[item_id] = {
                        "type": "link",
                        "title": title,
                        "url": url,
                        "checked": False,
                    }

    def on_click(self, event):
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if not item_id:
            return

        if column == "#1":
            data = self.node_map[item_id]
            new_state = not data["checked"]
            self.set_check_state(item_id, new_state)

    def set_check_state(self, item_id, state):
        data = self.node_map[item_id]
        data["checked"] = state

        char = "[x]" if state else "[ ]"

        self.tree.set(item_id, "check", char)

        if data["type"] == "folder":
            for child_id in self.tree.get_children(item_id):
                self.set_check_state(child_id, state)

    def export_json(self):
        export_data = []
        self.collect_checked_links("", export_data)

        try:
            with open(OUTPUT_FILE, "w") as f:
                json.dump(export_data, f, indent=2)
            messagebox.showinfo("Success", f"Exported to {OUTPUT_FILE}!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def collect_checked_links(self, parent_id, container):
        children = self.tree.get_children(parent_id)
        current_folder_links = []
        folder_title = "Uncategorized"

        if parent_id:
            folder_title = self.node_map[parent_id]["title"]

        for child_id in children:
            data = self.node_map[child_id]

            if data["type"] == "link" and data["checked"]:
                current_folder_links.append(
                    {"title": data["title"], "url": data["url"], "icon": "🔗"}
                )

            elif data["type"] == "folder":
                self.collect_checked_links(child_id, container)

        if current_folder_links:
            container.append({"category": folder_title, "links": current_folder_links})


if __name__ == "__main__":
    root = tk.Tk()
    app = BookmarkPickerApp(root)
    root.mainloop()
