"use client";

import { FormEvent, useState } from "react";
import { Check, Edit3, Plus, Trash2, X } from "lucide-react";

import { LineItem, LineItemPayload } from "../api/types";
import {
  formatMoney,
  formatPercent,
  formatSignedMoney,
  varianceClass
} from "../utils/money";

type Props = {
  lineItems: LineItem[];
  onCreate: (payload: LineItemPayload) => Promise<void>;
  onUpdate: (id: number, payload: LineItemPayload) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
};

const emptyLineItem: LineItemPayload = {
  department: "",
  category: "",
  description: "",
  budget_amount: "",
  actual_amount: "",
  notes: ""
};

export function LineItemsTable({
  lineItems,
  onCreate,
  onUpdate,
  onDelete
}: Props) {
  const [newItem, setNewItem] = useState<LineItemPayload>(emptyLineItem);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editItem, setEditItem] = useState<LineItemPayload>(emptyLineItem);
  const [saving, setSaving] = useState(false);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      await onCreate(newItem);
      setNewItem(emptyLineItem);
    } catch {
      // Parent component renders the API error banner.
    } finally {
      setSaving(false);
    }
  }

  async function saveEdit() {
    if (!editingId) return;
    setSaving(true);
    try {
      await onUpdate(editingId, editItem);
      setEditingId(null);
    } catch {
      // Parent component renders the API error banner.
    } finally {
      setSaving(false);
    }
  }

  function startEdit(item: LineItem) {
    setEditingId(item.id);
    setEditItem({
      department: item.department,
      category: item.category,
      description: item.description,
      budget_amount: item.budget_amount,
      actual_amount: item.actual_amount,
      notes: item.notes
    });
  }

  return (
    <div className="tableWrap">
      <table className="dataTable">
        <thead>
          <tr>
            <th>Department</th>
            <th>Category</th>
            <th>Budget</th>
            <th>Actual</th>
            <th>Variance</th>
            <th>Variance %</th>
            <th>Notes</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {lineItems.map((item) =>
            editingId === item.id ? (
              <tr key={item.id}>
                <EditableCells item={editItem} setItem={setEditItem} />
                <td className="actionCell">
                  <button
                    className="iconButton"
                    title="Save row"
                    aria-label="Save row"
                    onClick={() => void saveEdit()}
                    disabled={saving}
                  >
                    <Check size={16} />
                  </button>
                  <button
                    className="iconButton"
                    title="Cancel edit"
                    aria-label="Cancel edit"
                    onClick={() => setEditingId(null)}
                  >
                    <X size={16} />
                  </button>
                </td>
              </tr>
            ) : (
              <tr key={item.id}>
                <td>{item.department}</td>
                <td>{item.category}</td>
                <td>{formatMoney(item.budget_amount)}</td>
                <td>{formatMoney(item.actual_amount)}</td>
                <td className={varianceClass(item.variance)}>
                  {formatSignedMoney(item.variance)}
                </td>
                <td className={varianceClass(item.variance)}>
                  {formatPercent(item.variance_percent)}
                </td>
                <td className="notesCell">{item.notes || "—"}</td>
                <td className="actionCell">
                  <button
                    className="iconButton"
                    type="button"
                    title="Edit row"
                    aria-label={`Edit ${item.department} ${item.category}`}
                    onClick={() => startEdit(item)}
                  >
                    <Edit3 size={16} />
                  </button>
                  <button
                    className="iconButton dangerButton"
                    type="button"
                    title="Delete row"
                    aria-label={`Delete ${item.department} ${item.category}`}
                    onClick={() => onDelete(item.id)}
                  >
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            )
          )}
          {!lineItems.length && (
            <tr>
              <td colSpan={8} className="emptyCell">
                Add at least one line item to analyze this scenario.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <form className="inlineForm" onSubmit={handleCreate}>
        <Field
          label="Department"
          value={newItem.department}
          onChange={(value) => setNewItem({ ...newItem, department: value })}
          required
        />
        <Field
          label="Category"
          value={newItem.category}
          onChange={(value) => setNewItem({ ...newItem, category: value })}
          required
        />
        <Field
          label="Budget"
          value={newItem.budget_amount}
          onChange={(value) => setNewItem({ ...newItem, budget_amount: value })}
          type="number"
          required
        />
        <Field
          label="Actual"
          value={newItem.actual_amount}
          onChange={(value) => setNewItem({ ...newItem, actual_amount: value })}
          type="number"
          required
        />
        <Field
          label="Notes"
          value={newItem.notes || ""}
          onChange={(value) => setNewItem({ ...newItem, notes: value })}
        />
        <button className="primaryButton inlineSubmit" type="submit" disabled={saving}>
          <Plus size={16} />
          {saving ? "Saving..." : "Add"}
        </button>
      </form>
    </div>
  );
}

function EditableCells({
  item,
  setItem
}: {
  item: LineItemPayload;
  setItem: (item: LineItemPayload) => void;
}) {
  return (
    <>
      <td>
        <input
          aria-label="Department"
          value={item.department}
          onChange={(event) => setItem({ ...item, department: event.target.value })}
        />
      </td>
      <td>
        <input
          aria-label="Category"
          value={item.category}
          onChange={(event) => setItem({ ...item, category: event.target.value })}
        />
      </td>
      <td>
        <input
          aria-label="Budget amount"
          type="number"
          value={item.budget_amount}
          onChange={(event) =>
            setItem({ ...item, budget_amount: event.target.value })
          }
        />
      </td>
      <td>
        <input
          aria-label="Actual amount"
          type="number"
          value={item.actual_amount}
          onChange={(event) =>
            setItem({ ...item, actual_amount: event.target.value })
          }
        />
      </td>
      <td colSpan={2} className="muted">
        Recalculated after save
      </td>
      <td>
        <input
          aria-label="Notes"
          value={item.notes || ""}
          onChange={(event) => setItem({ ...item, notes: event.target.value })}
        />
      </td>
    </>
  );
}

function Field({
  label,
  value,
  onChange,
  required,
  type = "text"
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  type?: string;
}) {
  return (
    <label>
      <span>{label}</span>
      <input
        type={type}
        step={type === "number" ? "0.01" : undefined}
        required={required}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}
