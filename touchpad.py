import math


def distance2(pos1, pos2):
    x_diff = pos1[0][0] - pos2[0][0]
    y_diff = pos1[0][1] - pos2[0][1]
    return x_diff * x_diff + y_diff * y_diff


def merge(pos1, pos2):
    return ((pos1[0][0] + pos2[0][0]) / 2, (pos1[0][1] + pos2[0][1]) / 2), pos1[1] + pos2[1]


def absolute_to_relative(val_x, val_y, x_axis, y_axis, angle):
    """ shift and rotate position to fit the relative coordinate """
    x = val_x - x_axis
    y = val_y - y_axis
    print(x, y)
    return x * math.cos(angle) - y * math.sin(angle), x * math.sin(angle) + y * math.cos(angle)


class Hand:
    """ each finger has structure ((center_x, center_y), size) """
    def __init__(self, palm):
        self.palm = palm
        self.fingers = []
        self.thumb = None
        self.is_left = None  # whether this is the left hand
        self.dir = (0.0, 0.0)
        self.sep = 0.0

    def add_finger(self, finger):
        self.fingers.append(finger)

    def formulate(self):
        # separates thumb from fingers, decides self.left, self.dir and self.sep
        self.fingers = sorted(self.fingers, key=lambda x: x[1], reverse=True)
        self.thumb = self.fingers.pop(0)

        self.fingers = sorted(self.fingers, key=lambda x: distance2(x, self.thumb))
        f_1 = self.fingers[0]
        f_34 = merge(self.fingers[2], self.fingers[3])
        self.dir = float(f_34[0][1] - f_1[0][1]), float(f_34[0][0] - f_1[0][0])
        thumb_dir = float(self.thumb[0][1] - f_1[0][1]), float(self.thumb[0][0] - f_1[0][0])
        angle = math.atan2(thumb_dir[1], thumb_dir[0]) - math.atan2(self.dir[1], self.dir[0])
        self.is_left = -math.pi < angle < 0 or angle > math.pi

        for i in range(len(self.fingers) - 1):
            self.sep += math.sqrt(float(distance2(self.fingers[i], self.fingers[1 + i])))
        self.sep = self.sep / 4.0 * 0.8

    def get_key(self, pos):
        angle = -math.atan2(self.dir[1], self.dir[0]) + (math.pi if self.is_left else 0)
        x, y = absolute_to_relative(pos[0][0], -pos[0][1], self.fingers[0][0][0], -self.fingers[0][0][1], angle)
        print(x, y)
        if x >= self.sep * 1.5:
            return 'Q'
        elif x <= -self.sep * 1.5:
            return 'Z'
        else:
            return 'A'


class Touchpad:
    def __init__(self):
        self.empty_image = []
        self.current_image = None
        self.count = 0
        self.left = None
        self.right = None

    def process_image(self, image):
        self.current_image = image
        if self.count >= 10:
            fingers = sorted(self.get_fingers(), key=lambda x: x[1], reverse=True)
            if len(fingers) >= 12:
                self.separate_hands(fingers)
            elif self.left and self.right:
                for i in fingers:
                    key1 = self.left.get_key(i)
                    key2 = self.right.get_key(i)
                    # print key1 if key1 else key2,

        else:
            self.empty_image.append(self.current_image)
            if self.count == 9:
                average = []
                for j in range(len(self.empty_image[0])):
                    average.append([])
                    for k in range(len(self.empty_image[0][j])):
                        average[j].append(sum(self.empty_image[i][j][k] for i in range(len(self.empty_image))) / 10)
                self.empty_image = average
            self.count += 1

    def get_fingers(self):
        # gets a 2D_list of booleans that represents finger presses
        hands_on = []
        for j in range(len(self.empty_image)):
            hands_on.append([])
            for k in range(len(self.empty_image[j])):
                hands_on[j].append(self.empty_image[j][k] - self.current_image[j][k] >= 40)

        # gets an list of fingers of the structure ((center_x, center_y), size)
        segments = []
        mapping = {}
        for i in range(len(hands_on)):
            for j in range(len(hands_on[i])):
                if hands_on[i][j]:
                    mapped = False
                    directions = []
                    if i > 0:
                        if j > 0:
                            directions.append((-1, -1))
                        elif j < len(hands_on[i]) - 1:
                            directions.append((-1, 1))
                        directions.append((-1, 0))
                    if j > 0:
                        directions.append((0, -1))
                    for k in directions:
                        if not mapped and mapping.get((i + k[0], j + k[1])):
                            mapping[(i, j)] = mapping[(i + k[0], j + k[1])]
                            segments[mapping[(i + k[0], j + k[1])]].append((i, j))
                            mapped = True
                    if not mapped:
                        segments.append([(i, j)])
                        mapping[(i, j)] = len(segments) - 1
        for s in range(len(segments)):
            for (i, j) in segments[s]:
                unique = True
                directions = []
                if i < len(hands_on) - 1:
                    if j > 0:
                        directions.append((1, -1))
                    elif j < len(hands_on[i]) - 1:
                        directions.append((1, 1))
                    directions.append((1, 0))
                if j < len(hands_on[i]) - 1:
                    directions.append((0, 1))
                for t in range(len(segments)):
                    for k in directions:
                        if unique and t != s and (i + k[0], j + k[1]) in segments[t]:
                            segments[t] += segments[s]
                            unique = False
                if not unique:
                    segments[s] = []
        fingers = []
        for s in segments:
            if s:
                fingers.append((sorted(s, key=lambda x: x[1])[int(len(s) / 2)], len(s)))
        return fingers

    def separate_hands(self, fingers):
        # separate all fingers into two hands, different cases for 12 / 13 / 14 detected positions
        palm1, palm2 = None, None
        if len(fingers) == 12:
            palm1 = fingers[0]
            palm2 = fingers[1]
        elif len(fingers) == 13:
            d1 = distance2(fingers[0], fingers[1])
            d2 = distance2(fingers[0], fingers[2])
            d3 = distance2(fingers[1], fingers[2])
            ranking = sorted((d1, d2, d3))
            if ranking[0] == d1:
                palm1 = merge(fingers[0], fingers[1])
                palm2 = fingers[2]
            if ranking[0] == d2:
                palm1 = merge(fingers[0], fingers[2])
                palm2 = fingers[1]
            if ranking[0] == d3:
                palm1 = merge(fingers[1], fingers[2])
                palm2 = fingers[0]
            fingers.pop(2)
        elif len(fingers) == 14:
            d1 = distance2(fingers[0], fingers[1])
            d2 = distance2(fingers[0], fingers[2])
            d3 = distance2(fingers[0], fingers[3])
            d4 = distance2(fingers[1], fingers[2])
            d5 = distance2(fingers[1], fingers[3])
            d6 = distance2(fingers[2], fingers[3])
            ranking = sorted((d1 + d6, d2 + d5, d3 + d4))
            if ranking[0] == d1 + d6:
                palm1 = merge(fingers[0], fingers[1])
                palm2 = merge(fingers[2], fingers[3])
            if ranking[0] == d2 + d5:
                palm1 = merge(fingers[0], fingers[2])
                palm2 = merge(fingers[1], fingers[3])
            if ranking[0] == d3 + d4:
                palm1 = merge(fingers[0], fingers[3])
                palm2 = merge(fingers[1], fingers[2])
            fingers.pop(3)
            fingers.pop(2)
        fingers.pop(1)
        fingers.pop(0)
        hand1 = Hand(palm1)
        hand2 = Hand(palm2)
        for i in fingers:
            if distance2(i, hand1.palm) < distance2(i, hand2.palm):
                hand1.add_finger(i)
            else:
                hand2.add_finger(i)
        if len(hand1.fingers) < 5 or len(hand2.fingers) < 5:
            return
        hand1.formulate()
        hand2.formulate()
        if hand1.is_left:
            self.left = hand1
            self.right = hand2
        else:
            self.left = hand2
            self.right = hand1

    def reset(self):
        self.empty_image = []
        self.current_image = None
        self.count = 0