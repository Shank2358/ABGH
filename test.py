
import utils.gpu as gpu
from modelR.GGHL import GGHL
from tensorboardX import SummaryWriter
from evalR.evaluatorGGHL import Evaluator
import argparse
import os
import config.config as cfg
import time
import logging
from utils.utils_coco import *
from utils.log import Logger
from torch.cuda import amp
from copy import deepcopy


class Tester(object):
    def __init__(self, weight_path=None, gpu_id=0, visiual=None, eval=False):
        self.img_size = cfg.TEST["TEST_IMG_SIZE"]
        self.__num_class = cfg.DATA["NUM"]
        self.__conf_threshold = cfg.TEST["CONF_THRESH"]
        self.__nms_threshold = cfg.TEST["NMS_THRESH"]
        self.__device = gpu.select_device(gpu_id, force_cpu=False)
        self.__multi_scale_test = cfg.TEST["MULTI_SCALE_TEST"]
        self.__flip_test = cfg.TEST["FLIP_TEST"]
        self.__classes = cfg.DATA["CLASSES"]

        self.__visiual = visiual
        self.__eval = eval
        self.__model = GGHL().to(self.__device)  # Single GPU

        '''
        net_model = ABGH()
        if torch.cuda.device_count() >1: ## Multi GPUs
            print("Let's use", torch.cuda.device_count(), "GPUs!")
            net_model = torch.nn.DataParallel(net_model) ## Multi GPUs
            self.__model = net_model.to(self.__device)
        elif torch.cuda.device_count() ==1:
            self.__model = net_model.to(self.__device)
        '''
        self.__load_model_weights(weight_path)

    def __load_model_weights(self, weight_path):
        print("loading weight file from : {}".format(weight_path))
        weight = os.path.join(weight_path)
        chkpt = torch.load(weight, map_location=self.__device)
        #prnt(chkpt['model'])
        self.__model.load_state_dict(chkpt)
        # print(self.__model)
        del chkpt


    def test(self):
        global logger
        logger.info("***********Start Evaluation****************")
        mAP = 0
        mRecall = 0
        mPrecision = 0
        if self.__eval and cfg.TEST["EVAL_TYPE"] == 'VOC':
            with torch.no_grad():
                APs, inference_time = Evaluator(self.__model).APs_voc()
                for i in APs:
                    print("{} --> AP : {}".format(i, APs[i]))
                    mAP += APs[i]
                mAP = mAP / self.__num_class
                logger.info('mAP:{}'.format(mAP))
                logger.info("inference time: {:.2f} ms".format(inference_time))
                writer.add_scalar('test/VOCmAP', mAP)
                #speed = self.inference_time / len(img_inds) / cfg.TEST["NUMBER_WORKERS"]
                # print("Speed: ", self.inference_time)



if __name__ == "__main__":
    global logger
    parser = argparse.ArgumentParser()
    parser.add_argument('--weight_path', type=str, default='weight/GGHL_darknet53_fpn3_DOTA_76.95.pt', help='weight file path')
    parser.add_argument('--log_val_path', type=str, default='log/', help='weight file path')
    parser.add_argument('--visiual', type=str, default=None, help='test data path or None')
    parser.add_argument('--eval', action='store_true', default=True, help='eval flag')
    parser.add_argument('--gpu_id', type=int, default=0, help='gpu id')
    parser.add_argument('--log_path', type=str, default='log/', help='log path')
    opt = parser.parse_args()
    writer = SummaryWriter(logdir=opt.log_path + '/event')
    logger = Logger(log_file_name=opt.log_val_path + '/log_coco_test.txt', log_level=logging.DEBUG,
                    logger_name='GGHL').get_log()

    Tester(weight_path=opt.weight_path, gpu_id=opt.gpu_id, eval=opt.eval, visiual=opt.visiual).test()
