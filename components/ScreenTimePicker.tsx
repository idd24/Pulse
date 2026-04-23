import { useState } from 'react';
import {
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import DateTimePicker, {
  DateTimePickerAndroid,
} from '@react-native-community/datetimepicker';

import { SCREEN_TIME_MINUTES } from '@/lib/checkinOptions';

type Props = {
  hours: number;
  minutes: number;
  onChange: (h: number, m: number) => void;
};

const MAX_HOURS = 16;

// Snap minutes to {0,15,30,45}; carry into hours if rounded up to 60.
function snap(h: number, m: number): [number, number] {
  const rounded = Math.round(m / 15) * 15;
  if (rounded === 60) return [Math.min(MAX_HOURS, h + 1), 0];
  return [Math.min(MAX_HOURS, h), rounded];
}

function dateFromHM(h: number, m: number) {
  const d = new Date();
  d.setHours(h, m, 0, 0);
  return d;
}

export function ScreenTimePicker({ hours, minutes, onChange }: Props) {
  const [modalOpen, setModalOpen] = useState(false);
  const [draft, setDraft] = useState({ h: hours, m: minutes });

  if (Platform.OS === 'web') {
    return <WebStepper hours={hours} minutes={minutes} onChange={onChange} />;
  }

  function openPicker() {
    if (Platform.OS === 'android') {
      DateTimePickerAndroid.open({
        value: dateFromHM(hours, minutes),
        mode: 'time',
        is24Hour: true,
        onChange: (_evt, d) => {
          if (!d) return;
          const [h, m] = snap(d.getHours(), d.getMinutes());
          onChange(h, m);
        },
      });
      return;
    }
    setDraft({ h: hours, m: minutes });
    setModalOpen(true);
  }

  function commit() {
    const [h, m] = snap(draft.h, draft.m);
    onChange(h, m);
    setModalOpen(false);
  }

  return (
    <View>
      <Pressable style={styles.field} onPress={openPicker}>
        <Text style={styles.fieldText}>
          {hours}h {minutes}m
        </Text>
        <Text style={styles.chevron}>▾</Text>
      </Pressable>

      <Modal
        visible={modalOpen}
        transparent
        animationType="slide"
        onRequestClose={() => setModalOpen(false)}
      >
        <Pressable style={styles.backdrop} onPress={() => setModalOpen(false)} />
        <View style={styles.sheet}>
          <View style={styles.sheetHeader}>
            <Pressable onPress={() => setModalOpen(false)} hitSlop={10}>
              <Text style={styles.headerCancel}>Cancel</Text>
            </Pressable>
            <Text style={styles.headerTitle}>Screen time</Text>
            <Pressable onPress={commit} hitSlop={10}>
              <Text style={styles.headerDone}>Done</Text>
            </Pressable>
          </View>
          <DateTimePicker
            value={dateFromHM(draft.h, draft.m)}
            mode="countdown"
            display="spinner"
            minuteInterval={15}
            onChange={(_evt, d) => {
              if (!d) return;
              setDraft({ h: d.getHours(), m: d.getMinutes() });
            }}
            textColor="#fff"
            themeVariant="dark"
          />
        </View>
      </Modal>
    </View>
  );
}

function WebStepper({ hours, minutes, onChange }: Props) {
  return (
    <View style={styles.webRow}>
      <Stepper
        label="h"
        value={hours}
        onDec={() => onChange(Math.max(0, hours - 1), minutes)}
        onInc={() => onChange(Math.min(MAX_HOURS, hours + 1), minutes)}
      />
      <Stepper
        label="m"
        value={minutes}
        onDec={() => onChange(hours, stepMinute(minutes, -1))}
        onInc={() => onChange(hours, stepMinute(minutes, 1))}
      />
    </View>
  );
}

function stepMinute(current: number, dir: 1 | -1) {
  const i = SCREEN_TIME_MINUTES.indexOf(
    current as (typeof SCREEN_TIME_MINUTES)[number],
  );
  const base = i < 0 ? 0 : i;
  const next =
    (base + dir + SCREEN_TIME_MINUTES.length) % SCREEN_TIME_MINUTES.length;
  return SCREEN_TIME_MINUTES[next];
}

function Stepper({
  label,
  value,
  onDec,
  onInc,
}: {
  label: string;
  value: number;
  onDec: () => void;
  onInc: () => void;
}) {
  return (
    <View style={styles.stepper}>
      <Pressable style={styles.stepperBtn} onPress={onDec}>
        <Text style={styles.stepperBtnText}>−</Text>
      </Pressable>
      <Text style={styles.stepperValue}>
        {value}
        {label}
      </Text>
      <Pressable style={styles.stepperBtn} onPress={onInc}>
        <Text style={styles.stepperBtnText}>+</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  field: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#1f2328',
    borderRadius: 10,
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  fieldText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '500',
  },
  chevron: {
    color: '#9ca3af',
    fontSize: 14,
  },
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
  },
  sheet: {
    backgroundColor: '#25292e',
    paddingBottom: 24,
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
  },
  sheetHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#333942',
  },
  headerTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  headerCancel: {
    color: '#9ca3af',
    fontSize: 16,
  },
  headerDone: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  webRow: {
    flexDirection: 'row',
    gap: 12,
  },
  stepper: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#1f2328',
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  stepperBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#2d333b',
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepperBtnText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  stepperValue: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '500',
    minWidth: 40,
    textAlign: 'center',
  },
});
