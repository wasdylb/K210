import sensor, image, time, lcd
from FingerBitShield import *
from Maix import GPIO
from fpioa_manager import fm

fm.register(23, fm.fpioa.GPIOHS7, force=True)
led_bl = GPIO(GPIO.GPIOHS7, GPIO.OUT)
led_bl.value(1)

#按钮初始化，设置两按钮为上拉模式
fm.register(37, fm.fpioa.GPIOHS6, force=True)
fm.register(36, fm.fpioa.GPIOHS5, force=True)
key1 = GPIO(GPIO.GPIOHS6, GPIO.PULL_UP)
key2 = GPIO(GPIO.GPIOHS5, GPIO.PULL_UP)

motor = motorPro()#初始化电机
motor.setSpeed(0,0)#设置速度为0

lcd.init(freq=60000000)#初始化屏幕
lcd.rotation(1)#旋转屏幕
sensor.reset() #重置并初始化传感器。
sensor.set_pixformat(sensor.RGB565)#将像素格式设置为RGB565
sensor.set_hmirror(0)#摄像头水平镜像设置
sensor.set_vflip(1)  #摄像头垂直镜像设置
sensor.set_framesize(sensor.QQVGA) #设置图像格式QQVGA(160*120)
sensor.skip_frames(time = 2000) #等待设置生效

ROI=(60,40,40,40)#感兴趣区域
DEVIATION = 25   #颜色偏差值
AREX_MAX = 10000 #图像最大面积
AREX_MIN = 2000  #图像最小面积

again = 0

# 限制函数，将某个值限制在一定区间内
# 第一个参数：要限制的数
# 第二个参数：数的最小值
# 第三个参数：数的最大值
def constrain(val, min_val, max_val):
    if val < min_val:
        return min_val
    if val > max_val:
        return max_val
    return val

# 数值映射函数，将某区间的值映射到另一区间
# 第一个参数：要映射的数
# 第二个参数：输入数据的最小值
# 第三个参数：输入数据的最大值
# 第四个参数：输出数据的最小值
# 第无个参数：输出数据的最大值
def map(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

#key1按钮没按下一直执行
while(key1.value()):
    #获取图像
    img = sensor.snapshot()
    #统计图像信息
    statistics=img.get_statistics(roi=ROI)
    #打印图像LAB颜色众数
    print(statistics.l_mode(),statistics.a_mode(),statistics.b_mode())
    #存储颜色区间
    threshold=(statistics.l_mode()-DEVIATION,statistics.l_mode()+DEVIATION,statistics.a_mode()-DEVIATION,statistics.a_mode()+DEVIATION,statistics.b_mode()-DEVIATION,statistics.b_mode()+DEVIATION)
    #感兴趣区域画框
    img.draw_rectangle(ROI,color = (255, 0, 0))
    #在lcd屏幕上显示
    lcd.display(img)

disappeardir = 0
while(True):
    #获取图像
    img = sensor.snapshot()
    
    if key2.value() == 0:#key2按钮按下，重新设置颜色
        again = 1
        motor.setSpeed(0,0)#关闭电机
    if key1.value() == 0:#key1按钮按下，重新识别颜色
        again = 0


    if again == 0:
        blobs =img.find_blobs([threshold], pixels_threshold=200, area_threshold=2000, merge=True)
        if not blobs:
            #计算时间
            delta = time.ticks_diff(time.ticks_ms(), start)
            #print(delta)
            if delta<3000:#未超时
                if disappeardir == -1:#右边消失
                    motor.setSpeed(60,-60)#原地右转找色块
                elif disappeardir == 1:#左边消失
                    motor.setSpeed(-60,60)#原地左转找色块
                else:
                    motor.setSpeed(0,0)
            else:
                motor.setSpeed(0,0)

        for blob in blobs:
            start = time.ticks_ms()
            img.draw_cross(blob.cx(), blob.cy())
            img.draw_rectangle(blob.rect())
            # 获取矩形面积
            area = blob.area()
            # 限制矩形面积
            area = constrain(area, AREX_MIN, AREX_MAX)
            ## 将面积映射到一定范围，我们把他认为是距离，
            # 面积越小距离正值越大（色块越远前进速度越大）
            # 面积越大距离负值越大（色块越近后退速度越大）
            distance = map(area, AREX_MIN, AREX_MAX, 130, -130)
            ##计算在水平坐标上的偏移量
            # 图片像素160*120，中心偏左的为负数，中心偏右的为正数
            tilt_error = blob.cx() - 80
            # 将水平偏移量限制在一个区域
            tilt_error = constrain(tilt_error, -60, 60)

            ##根据距离与水平偏移量计算速度
            # 距离决定了前进的速度
            # 水平偏移量决定了拐弯大小，0.9是拐弯大小系数，值越大拐的幅度越小
            leftspeed = int(distance - tilt_error*0.9)
            rightspeed = int(distance + tilt_error*0.9)

            if(distance<110 and distance>-110 and tilt_error<20 and tilt_error>-20):
                leftspeed = 0
                rightspeed = 0
            else:
                # 限制速度不超出最大范围之内
                leftspeed = constrain(leftspeed, -255, 255)
                rightspeed = constrain(rightspeed, -255, 255)
            motor.setSpeed(leftspeed,rightspeed)

            if tilt_error < -30:
                disappeardir = -1
            elif tilt_error > 30:
                disappeardir = 1
            else:
                disappeardir = 0
            #print("area",area," distance:",distance," tilt_error:",tilt_error," disappeardir:",disappeardir,"speed:",leftspeed,",",rightspeed)
    else:
        motor.setSpeed(0,0)
        statistics=img.get_statistics(roi=ROI)
        img.draw_rectangle(ROI,color = (255, 0, 0))
        print(statistics.l_mode(),statistics.a_mode(),statistics.b_mode())
        threshold=(statistics.l_mode()-DEVIATION,statistics.l_mode()+DEVIATION,statistics.a_mode()-DEVIATION,statistics.a_mode()+DEVIATION,statistics.b_mode()-DEVIATION,statistics.b_mode()+DEVIATION)
    lcd.display(img)