import Slider from '@react-native-community/slider';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  ACTIVITIES,
  ENERGY_COLORS,
  ENERGY_LABELS,
  MOOD_EMOJI,
  type ActivityId,
} from '@/lib/checkinOptions';
import {
  getTodayCheckin,
  getTodayScreentime,
  saveCheckin,
  saveScreentime,
  type CheckinResponse,
} from '@/lib/checkins';

const SLIDER_MAX_MINUTES = 480; // 8h per-category cap
const SLIDER_STEP = 15;

function formatMinutes(m: number) {
  const h = Math.floor(m / 60);
  const min = m % 60;
  if (h === 0) return `${min}m`;
  if (min === 0) return `${h}h`;
  return `${h}h ${min}m`;
}

export default function CheckinScreen() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [justSaved, setJustSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [existing, setExisting] = useState<CheckinResponse | null>(null);

  const [mood, setMood] = useState<number | null>(null);
  const [energy, setEnergy] = useState<number | null>(null);
  const [activities, setActivities] = useState<Set<ActivityId>>(new Set());
  const [social, setSocial] = useState(0);
  const [entertainment, setEntertainment] = useState(0);
  const [productivity, setProductivity] = useState(0);

  useEffect(() => {
    Promise.all([getTodayCheckin(), getTodayScreentime()])
      .then(([checkin, screentime]) => {
        if (checkin) {
          setExisting(checkin);
          setMood(checkin.mood);
          setEnergy(checkin.energy);
          setActivities(new Set(checkin.activities));
        }
        if (screentime) {
          setSocial(screentime.social);
          setEntertainment(screentime.entertainment);
          setProductivity(screentime.productivity);
        }
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => setLoading(false));
  }, []);

  function toggleActivity(id: ActivityId) {
    setActivities((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function onSave() {
    if (mood === null || energy === null) return;
    setError(null);
    setSaving(true);
    setJustSaved(false);
    try {
      const [checkin] = await Promise.all([
        saveCheckin({ mood, energy, activities: Array.from(activities) }),
        saveScreentime({ social, entertainment, productivity }),
      ]);
      setExisting(checkin);
      setJustSaved(true);
      setTimeout(() => setJustSaved(false), 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator color="#fff" />
      </View>
    );
  }

  const disabled = saving || mood === null || energy === null;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
    >
      <Text style={styles.title}>
        {existing ? "Today's check-in" : 'Daily check-in'}
      </Text>
      <Text style={styles.subtitle}>A quick tap on each — takes under a minute.</Text>

      <Section label="How's your mood?">
        <View style={styles.emojiRow}>
          {MOOD_EMOJI.map((emoji, i) => (
            <Pressable
              key={i}
              onPress={() => setMood(i)}
              style={[styles.emojiButton, mood === i && styles.emojiSelected]}
            >
              <Text style={styles.emoji}>{emoji}</Text>
            </Pressable>
          ))}
        </View>
      </Section>

      <Section label="Energy level">
        <View style={styles.energyRow}>
          {ENERGY_COLORS.map((color, i) => {
            const selected = energy === i;
            return (
              <Pressable
                key={i}
                onPress={() => setEnergy(i)}
                style={[
                  styles.energyPill,
                  { backgroundColor: selected ? color : 'transparent', borderColor: color },
                  selected && styles.energyPillSelected,
                ]}
              >
                <Text style={[styles.energyText, selected && styles.energyTextSelected]}>
                  {i + 1}
                </Text>
              </Pressable>
            );
          })}
        </View>
        <View style={styles.energyLabels}>
          <Text style={styles.hint}>{ENERGY_LABELS[0]}</Text>
          <Text style={styles.hint}>{ENERGY_LABELS[1]}</Text>
        </View>
      </Section>

      <Section label="What did you do today?" sublabel="Tap any that apply">
        <View style={styles.chipGrid}>
          {ACTIVITIES.map((a) => {
            const selected = activities.has(a.id);
            return (
              <Pressable
                key={a.id}
                onPress={() => toggleActivity(a.id)}
                style={[styles.chip, selected && styles.chipSelected]}
              >
                <Text style={[styles.chipText, selected && styles.chipTextSelected]}>
                  {selected ? '✓ ' : ''}
                  {a.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </Section>

      <Section label="Screen time by category" sublabel="Estimate minutes spent today">
        <SliderRow label="Social" value={social} onChange={setSocial} />
        <SliderRow
          label="Entertainment"
          value={entertainment}
          onChange={setEntertainment}
        />
        <SliderRow
          label="Productivity"
          value={productivity}
          onChange={setProductivity}
        />
      </Section>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Pressable
        style={[styles.button, disabled && styles.buttonDisabled]}
        onPress={onSave}
        disabled={disabled}
      >
        {saving ? (
          <ActivityIndicator color="#25292e" />
        ) : (
          <Text style={styles.buttonText}>
            {existing ? 'Update check-in' : 'Save check-in'}
          </Text>
        )}
      </Pressable>

      {justSaved ? <Text style={styles.saved}>✓ Saved</Text> : null}
    </ScrollView>
  );
}

function Section({
  label,
  sublabel,
  children,
}: {
  label: string;
  sublabel?: string;
  children: React.ReactNode;
}) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionLabel}>{label}</Text>
      {sublabel ? <Text style={styles.hint}>{sublabel}</Text> : null}
      {children}
    </View>
  );
}

function SliderRow({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <View style={styles.sliderRow}>
      <View style={styles.sliderHeader}>
        <Text style={styles.sliderLabel}>{label}</Text>
        <Text style={styles.sliderValue}>{formatMinutes(value)}</Text>
      </View>
      <Slider
        minimumValue={0}
        maximumValue={SLIDER_MAX_MINUTES}
        step={SLIDER_STEP}
        value={value}
        onValueChange={(v) => onChange(Math.round(v))}
        minimumTrackTintColor="#fff"
        maximumTrackTintColor="#333942"
        thumbTintColor="#fff"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#25292e',
  },
  content: {
    padding: 20,
    gap: 8,
    paddingBottom: 48,
  },
  loading: {
    flex: 1,
    backgroundColor: '#25292e',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '600',
  },
  subtitle: {
    color: '#9ca3af',
    fontSize: 14,
    marginBottom: 12,
  },
  section: {
    marginTop: 16,
    gap: 8,
  },
  sectionLabel: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  hint: {
    color: '#9ca3af',
    fontSize: 12,
  },
  emojiRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  emojiButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#1f2328',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  emojiSelected: {
    borderColor: '#fff',
    backgroundColor: '#2d333b',
  },
  emoji: {
    fontSize: 26,
  },
  energyRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 6,
  },
  energyPill: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
    borderWidth: 2,
  },
  energyPillSelected: {
    transform: [{ scale: 1.05 }],
  },
  energyText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  energyTextSelected: {
    color: '#111',
  },
  energyLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 2,
  },
  chipGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    backgroundColor: '#1f2328',
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  chipSelected: {
    backgroundColor: '#fff',
    borderColor: '#fff',
  },
  chipText: {
    color: '#d1d5db',
    fontSize: 14,
  },
  chipTextSelected: {
    color: '#25292e',
    fontWeight: '600',
  },
  sliderRow: {
    backgroundColor: '#1f2328',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
    gap: 4,
  },
  sliderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sliderLabel: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  sliderValue: {
    color: '#9ca3af',
    fontSize: 13,
  },
  button: {
    backgroundColor: '#fff',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 24,
  },
  buttonDisabled: {
    opacity: 0.4,
  },
  buttonText: {
    color: '#25292e',
    fontSize: 16,
    fontWeight: '600',
  },
  error: {
    color: '#f87171',
    fontSize: 14,
    marginTop: 16,
  },
  saved: {
    color: '#4ade80',
    fontSize: 14,
    textAlign: 'center',
    marginTop: 10,
  },
});
